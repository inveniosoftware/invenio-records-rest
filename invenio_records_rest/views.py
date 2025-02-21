# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API resources."""

import copy
import uuid
from collections import defaultdict
from functools import partial, wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
    url_for,
)
from flask.views import MethodView
from invenio_db import db
from invenio_i18n import gettext as _
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.decorators import require_content_types
from invenio_search import RecordsSearch
from invenio_search.engine import search as search_engine
from jsonpatch import JsonPatchException, JsonPointerException
from jsonschema.exceptions import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from webargs import ValidationError as WebargsValidationError
from webargs import fields, validate
from webargs.flaskparser import parser
from werkzeug.exceptions import BadRequest

from ._compat import wrap_links_factory
from .errors import (
    InvalidDataRESTError,
    InvalidQueryRESTError,
    JSONSchemaValidationError,
    PatchJSONFailureRESTError,
    PIDResolveRESTError,
    SearchPaginationRESTError,
    SuggestMissingContextRESTError,
    SuggestNoCompletionsRESTError,
    UnhandledSearchError,
    UnsupportedMediaRESTError,
)
from .links import default_links_factory
from .proxies import current_records_rest
from .query import es_search_factory
from .utils import obj_or_import_string


def search_query_parsing_exception_handler(error):
    """Handle query parsing exceptions from the search engine."""
    description = _("The syntax of the search query is invalid.")
    return InvalidQueryRESTError(description=description).get_response()


def create_error_handlers(blueprint, error_handlers_registry=None):
    """Create error handlers on blueprint.

    :params blueprint: Records API blueprint.
    :params error_handlers_registry: Configuration of error handlers per
        exception or HTTP status code and view name.

        The dictionary has the following structure:

        .. code-block:: python

            {
                SomeExceptionClass: {
                    'recid_list': 'path.to.error_handler_function_foo',
                    'recid_item': 'path.to.error_handler_function_foo',
                },
                410: {
                    'custom_pid_list': 'path.to.error_handler_function_bar',
                    'custom_pid_item': 'path.to.error_handler_function_bar',
                    'recid_item': 'path.to.error_handler_function_baz',
                    'recid_list': 'path.to.error_handler_function_baz',
                },
            }
    :returns: Configured blueprint.
    """
    error_handlers_registry = error_handlers_registry or {}

    # Catch record validation errors
    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        """Catch validation errors."""
        return JSONSchemaValidationError(error=error).get_response()

    @blueprint.errorhandler(search_engine.RequestError)
    def search_badrequest_error(error):
        """Catch errors of the search engine."""
        handlers = current_app.config["RECORDS_REST_SEARCH_ERROR_HANDLERS"]
        cause_types = {c["type"] for c in error.info["error"]["root_cause"]}

        for cause_type, handler in handlers.items():
            if cause_type in cause_types:
                return handler(error)

        # Default exception for unhandled errors
        exception = UnhandledSearchError()
        current_app.logger.exception(error)  # Log the original stacktrace
        return exception.get_response()

    for exc_or_code, handlers in error_handlers_registry.items():
        # Build full endpoint names and resolve handlers
        handlers = {
            ".".join([blueprint.name, view_name]): obj_or_import_string(func)
            for view_name, func in handlers.items()
        }

        def dispatch_handler(error):
            def default_handler(e):
                raise e

            return handlers.get(request.endpoint, default_handler)(error)

        blueprint.register_error_handler(exc_or_code, dispatch_handler)

    return blueprint


def create_blueprint_from_app(app):
    """Create Invenio-Records-REST blueprint from a Flask application.

    .. note::

        This function assumes that the application has loaded all extensions
        that want to register REST endpoints via the ``RECORDS_REST_ENDPOINTS``
        configuration variable.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    return create_blueprint(app.config.get("RECORDS_REST_ENDPOINTS"))


def create_blueprint(endpoints):
    """Create Invenio-Records-REST blueprint.

    :params endpoints: Dictionary representing the endpoints configuration.
    :returns: Configured blueprint.
    """
    endpoints = endpoints or {}

    blueprint = Blueprint(
        "invenio_records_rest",
        __name__,
        url_prefix="",
    )

    error_handlers_registry = defaultdict(dict)
    for endpoint, options in endpoints.items():
        error_handlers = options.pop("error_handlers", {})
        for rule in create_url_rules(endpoint, **options):
            for exc_or_code, handler in error_handlers.items():
                view_name = rule["view_func"].__name__
                error_handlers_registry[exc_or_code][view_name] = handler
            blueprint.add_url_rule(**rule)

    return create_error_handlers(blueprint, error_handlers_registry)


def create_url_rules(
    endpoint,
    list_route=None,
    item_route=None,
    pid_type=None,
    pid_minter=None,
    pid_fetcher=None,
    read_permission_factory_imp=None,
    create_permission_factory_imp=None,
    update_permission_factory_imp=None,
    delete_permission_factory_imp=None,
    list_permission_factory_imp=None,
    record_class=None,
    record_serializers=None,
    record_serializers_aliases=None,
    record_loaders=None,
    search_class=None,
    indexer_class=RecordIndexer,
    search_serializers=None,
    search_serializers_aliases=None,
    search_index=None,
    default_media_type=None,
    max_result_window=None,
    use_options_view=True,
    search_factory_imp=None,
    links_factory_imp=None,
    suggesters=None,
    default_endpoint_prefix=None,
    search_query_parser=None,
):
    """Create Werkzeug URL rules.

    :param endpoint: Name of endpoint.
    :param list_route: Record listing URL route. Required.
    :param item_route: Record URL route (must include ``<pid_value>`` pattern).
        Required.
    :param pid_type: Persistent identifier type for endpoint. Required.
    :param pid_minter: It identifies the registered minter name.
    :param pid_fetcher: It identifies the registered fetcher name.
    :param read_permission_factory_imp: Import path to factory that creates a
        read permission object for a given record.
    :param create_permission_factory_imp: Import path to factory that creates a
        create permission object for a given record.
    :param update_permission_factory_imp: Import path to factory that creates a
        update permission object for a given record.
    :param delete_permission_factory_imp: Import path to factory that creates a
        delete permission object for a given record.
    :param list_permission_factory_imp: Import path to factory that
        creates a list permission object for a given index/list.
    :param default_endpoint_prefix: ignored.
    :param record_class: A record API class or importable string used when
        creating new records.
    :param record_serializers: Serializers used for records.
    :param record_serializers_aliases: A mapping of values of the defined
        query arg (see `config.REST_MIMETYPE_QUERY_ARG_NAME`) to valid
        mimetypes for record item serializers: dict(alias -> mimetype).
    :param record_loaders: It contains the list of record deserializers for
        supported formats.
    :param search_class: Import path or class object for the object in charge
        of execute the search queries. The default search class is
        :class:`invenio_search.api.RecordsSearch`.
        For more information about resource loading, see the Search of
        the search engine DSL library.
    :param indexer_class: Import path or class object for the object in charge
        of indexing records. The default indexer is
        :class:`invenio_indexer.api.RecordIndexer`.
    :param search_serializers: Serializers used for search results.
    :param search_serializers_aliases: A mapping of values of the defined
        query arg (see `config.REST_MIMETYPE_QUERY_ARG_NAME`) to valid
        mimetypes for records search serializers: dict(alias -> mimetype).
    :param search_index: Name of the search index used when searching records.
    :param default_media_type: Default media type for both records and search.
    :param max_result_window: Maximum number of results that the search engine can
        provide for the given search index without use of scroll. This value
        should correspond to the search engine ``index.max_result_window`` value
        for the index.
    :param use_options_view: Determines if a special option view should be
        installed.
    :param search_factory_imp: Factory to parse queries.
    :param links_factory_imp: Factory for record links generation.
    :param suggesters: Suggester fields configuration.
    :param search_query_parser: Function that implements the query parser

    :returns: a list of dictionaries with can each be passed as keywords
        arguments to ``Blueprint.add_url_rule``.
    """
    assert list_route
    assert item_route
    assert pid_type
    assert search_serializers
    assert record_serializers

    read_permission_factory = obj_or_import_string(read_permission_factory_imp)
    create_permission_factory = obj_or_import_string(create_permission_factory_imp)
    update_permission_factory = obj_or_import_string(update_permission_factory_imp)
    delete_permission_factory = obj_or_import_string(delete_permission_factory_imp)
    list_permission_factory = obj_or_import_string(list_permission_factory_imp)
    links_factory = obj_or_import_string(
        links_factory_imp, default=default_links_factory
    )
    # For backward compatibility. Previous signature was links_factory(pid).
    if wrap_links_factory(links_factory):
        orig_links_factory = links_factory

        def links_factory(pid, record=None, **kwargs):
            return orig_links_factory(pid)

    record_class = obj_or_import_string(record_class, default=Record)
    search_class = obj_or_import_string(search_class, default=RecordsSearch)

    indexer_class = obj_or_import_string(indexer_class, default=None)

    search_class_kwargs = {}
    if search_index:
        search_class_kwargs["index"] = search_index
    else:
        search_index = search_class.Meta.index

    if search_class_kwargs:
        search_class = partial(search_class, **search_class_kwargs)

    if record_loaders:
        record_loaders = {
            mime: obj_or_import_string(func) for mime, func in record_loaders.items()
        }
    record_serializers = {
        mime: obj_or_import_string(func) for mime, func in record_serializers.items()
    }
    search_serializers = {
        mime: obj_or_import_string(func) for mime, func in search_serializers.items()
    }

    list_view = RecordsListResource.as_view(
        RecordsListResource.view_name.format(endpoint),
        minter_name=pid_minter,
        pid_type=pid_type,
        pid_fetcher=pid_fetcher,
        read_permission_factory=read_permission_factory,
        create_permission_factory=create_permission_factory,
        list_permission_factory=list_permission_factory,
        record_serializers=record_serializers,
        record_loaders=record_loaders,
        search_serializers=search_serializers,
        serializers_query_aliases=search_serializers_aliases,
        search_class=search_class,
        indexer_class=indexer_class,
        default_media_type=default_media_type,
        max_result_window=max_result_window,
        search_factory=(
            obj_or_import_string(search_factory_imp, default=es_search_factory)
        ),
        item_links_factory=links_factory,
        record_class=record_class,
        search_query_parser=search_query_parser,
    )
    item_view = RecordResource.as_view(
        RecordResource.view_name.format(endpoint),
        read_permission_factory=read_permission_factory,
        update_permission_factory=update_permission_factory,
        delete_permission_factory=delete_permission_factory,
        serializers=record_serializers,
        serializers_query_aliases=record_serializers_aliases,
        loaders=record_loaders,
        search_class=search_class,
        indexer_class=indexer_class,
        links_factory=links_factory,
        default_media_type=default_media_type,
    )

    views = [
        dict(rule=list_route, view_func=list_view),
        dict(rule=item_route, view_func=item_view),
    ]
    if suggesters:
        suggest_view = SuggestResource.as_view(
            SuggestResource.view_name.format(endpoint),
            suggesters=suggesters,
            search_class=search_class,
        )

        views.append(dict(rule=list_route + "_suggest", view_func=suggest_view))

    if use_options_view:
        options_view = RecordsListOptionsResource.as_view(
            RecordsListOptionsResource.view_name.format(endpoint),
            search_index=search_index,
            max_result_window=max_result_window,
            default_media_type=default_media_type,
            search_media_types=search_serializers.keys(),
            item_media_types=record_serializers.keys(),
        )
        return [
            dict(rule="{0}_options".format(list_route), view_func=options_view)
        ] + views
    return views


def pass_record(f):
    """Decorator to retrieve persistent identifier and record.

    This decorator will resolve the ``pid_value`` parameter from the route
    pattern and resolve it to a PID and a record, which are then available in
    the decorated function as ``pid`` and ``record`` kwargs respectively.
    """

    @wraps(f)
    def inner(self, pid_value, *args, **kwargs):
        try:
            pid, record = request.view_args["pid_value"].data
            return f(self, pid=pid, record=record, *args, **kwargs)
        except SQLAlchemyError:
            raise PIDResolveRESTError(pid_value)

    return inner


def verify_record_permission(permission_factory, record):
    """Check that the current user has the required permissions on record.

    In case the permission check fails, an Flask abort is launched.
    If the user was previously logged-in, a HTTP error 403 is returned.
    Otherwise, is returned a HTTP error 401.

    :param permission_factory: permission factory used to check permissions.
    :param record: record whose access is limited.
    """
    # Note, cannot be done in one line due overloading of boolean
    # operations permission object.
    if not permission_factory(record=record).can():
        from flask_login import current_user

        if not current_user.is_authenticated:
            abort(401)
        abort(403)


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the permission factory.
    """

    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, record=None, *args, **kwargs):
            permission_factory = getattr(self, factory_name) or getattr(
                current_records_rest, factory_name
            )

            # FIXME use context instead
            request._methodview = self

            if permission_factory:
                verify_record_permission(permission_factory, record)
            return f(self, record=record, *args, **kwargs)

        return need_record_permission_decorator

    return need_record_permission_builder


def _validate_pagination_args(args):
    if args.get("page") and args.get("from"):
        raise WebargsValidationError(
            _("The query parameters from and page must not be used at the same time."),
            field_names=["page", "from"],
        )


def use_paginate_args(default_size=25, max_results=10000):
    """Get and validate pagination arguments."""

    def decorator(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            _default_size = (
                default_size(self) if callable(default_size) else default_size
            )
            _max_results = max_results(self) if callable(max_results) else max_results

            try:
                req = parser.parse(
                    {
                        "page": fields.Int(
                            validate=validate.Range(min=1),
                        ),
                        "from": fields.Int(
                            load_from="from",
                            validate=validate.Range(min=1),
                        ),
                        "size": fields.Int(
                            validate=validate.Range(min=1), missing=_default_size
                        ),
                    },
                    locations=["querystring"],
                    validate=_validate_pagination_args,
                    error_status_code=400,
                )
            # For validation errors, webargs raises an enhanced BadRequest
            except BadRequest as err:
                raise SearchPaginationRESTError(
                    description=_("Invalid pagination parameters."),
                    errors=err.data.get("messages"),
                )

            # Default if neither page nor from is specified
            if not (req.get("page") or req.get("from")):
                req["page"] = 1

            if req.get("page"):
                req.update(
                    dict(
                        from_idx=(req["page"] - 1) * req["size"],
                        to_idx=req["page"] * req["size"],
                        links=dict(
                            prev={"page": req["page"] - 1},
                            self={"page": req["page"]},
                            next={"page": req["page"] + 1},
                        ),
                    )
                )
            elif req.get("from"):
                req.update(
                    dict(
                        from_idx=req["from"] - 1,
                        to_idx=req["from"] - 1 + req["size"],
                        links=dict(
                            prev={"from": max(1, req["from"] - req["size"])},
                            self={"from": req["from"]},
                            next={"from": req["from"] + req["size"]},
                        ),
                    )
                )

            if req["to_idx"] > _max_results:
                raise SearchPaginationRESTError(
                    description=(
                        _(
                            "Maximum number of %(count)s results have been reached.",
                            count=_max_results,
                        )
                    )
                )

            return f(self, pagination=req, *args, **kwargs)

        return inner

    return decorator


class RecordsListOptionsResource(MethodView):
    """Resource for displaying options about records list/item views."""

    view_name = "{0}_list_options"

    def __init__(
        self,
        search_index=None,
        max_result_window=None,
        default_media_type=None,
        search_media_types=None,
        item_media_types=None,
    ):
        """Initialize method view."""
        self.search_index = search_index
        self.max_result_window = max_result_window or 10000
        self.default_media_type = default_media_type
        self.item_media_types = item_media_types
        self.search_media_types = search_media_types

    def get(self):
        """Get options."""
        opts = current_app.config["RECORDS_REST_SORT_OPTIONS"].get(self.search_index)

        sort_fields = []
        if opts:
            for key, item in sorted(opts.items(), key=lambda x: x[1]["order"]):
                sort_fields.append(
                    {
                        key: dict(
                            title=item["title"],
                            default_order=item.get("default_order", "asc"),
                        )
                    }
                )

        return jsonify(
            dict(
                sort_fields=sort_fields,
                max_result_window=self.max_result_window,
                default_media_type=self.default_media_type,
                search_media_types=sorted(self.search_media_types),
                item_media_types=sorted(self.item_media_types),
            )
        )


class RecordsListResource(ContentNegotiatedMethodView):
    """Resource for records listing."""

    view_name = "{0}_list"

    def __init__(
        self,
        minter_name=None,
        pid_type=None,
        pid_fetcher=None,
        read_permission_factory=None,
        create_permission_factory=None,
        list_permission_factory=None,
        search_class=None,
        record_serializers=None,
        record_loaders=None,
        search_serializers=None,
        default_media_type=None,
        max_result_window=None,
        search_factory=None,
        item_links_factory=None,
        record_class=None,
        indexer_class=None,
        search_query_parser=None,
        **kwargs,
    ):
        """Constructor."""
        super().__init__(
            method_serializers={
                "GET": search_serializers,
                "POST": record_serializers,
            },
            default_method_media_type={
                "GET": default_media_type,
                "POST": default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs,
        )
        self.pid_type = pid_type
        self.minter = current_pidstore.minters[minter_name]
        self.pid_fetcher = current_pidstore.fetchers[pid_fetcher]
        self.read_permission_factory = read_permission_factory
        self.create_permission_factory = (
            create_permission_factory or current_records_rest.create_permission_factory
        )
        self.list_permission_factory = (
            list_permission_factory or current_records_rest.list_permission_factory
        )
        self.search_class = search_class
        self.max_result_window = max_result_window or 10000
        self.search_factory = partial(search_factory, self)
        self.item_links_factory = item_links_factory
        self.loaders = record_loaders or current_records_rest.loaders
        self.record_class = record_class or Record
        self.indexer_class = indexer_class
        self.search_query_parser = search_query_parser

    @need_record_permission("list_permission_factory")
    @use_paginate_args(
        default_size=lambda self: current_app.config.get(
            "RECORDS_REST_DEFAULT_RESULTS_SIZE", 10
        ),
        max_results=lambda self: self.max_result_window,
    )
    def get(self, pagination=None, **kwargs):
        """Search records.

        Permissions: the `list_permission_factory` permissions are
            checked.

        :returns: Search result containing hits and aggregations as
                  returned by invenio-search.
        """
        # Arguments that must be added in prev/next links
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search = search[pagination["from_idx"] : pagination["to_idx"]]
        search = search.extra(track_total_hits=True)

        search, qs_kwargs = self.search_factory(search, self.search_query_parser)
        urlkwargs.update(qs_kwargs)

        # Execute search
        search_result = search.execute()

        # Generate links for self/prev/next
        total = search_result.hits.total["value"]
        endpoint = ".{0}_list".format(
            current_records_rest.default_endpoint_prefixes[self.pid_type]
        )
        urlkwargs.update(size=pagination["size"], _external=True)

        links = {}

        def _link(name):
            urlkwargs.update(pagination["links"][name])
            links[name] = url_for(endpoint, **urlkwargs)

        _link("self")
        if pagination["from_idx"] >= 1:
            _link("prev")
        if pagination["to_idx"] < min(total, self.max_result_window):
            _link("next")

        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=search_result.to_dict(),
            links=links,
            item_links_factory=self.item_links_factory,
        )

    @need_record_permission("create_permission_factory")
    def post(self, **kwargs):
        """Create a record.

        Permissions: ``create_permission_factory``

        Procedure description:

        #. First of all, the `create_permission_factory` permissions are
            checked.

        #. Then, the record is deserialized by the proper loader.

        #. A second call to the `create_permission_factory` factory is done:
            it differs from the previous call because this time the record is
            passed as parameter.

        #. A `uuid` is generated for the record and the minter is called.

        #. The record class is called to create the record.

        #. The HTTP response is built with the help of the item link factory.

        :returns: The created record.
        """
        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        # Check permissions
        permission_factory = self.create_permission_factory
        if permission_factory:
            verify_record_permission(permission_factory, data)

        # Create uuid for record
        record_uuid = uuid.uuid4()
        # Create persistent identifier
        pid = self.minter(record_uuid, data=data)
        # Create record
        record = self.record_class.create(data, id_=record_uuid)

        db.session.commit()

        # Index the record
        if self.indexer_class:
            self.indexer_class().index(record)

        response = self.make_response(
            pid, record, 201, links_factory=self.item_links_factory
        )

        # Add location headers
        endpoint = ".{0}_item".format(
            current_records_rest.default_endpoint_prefixes[pid.pid_type]
        )
        location = url_for(endpoint, pid_value=pid.pid_value, _external=True)
        response.headers.extend(dict(location=location))
        return response


class RecordResource(ContentNegotiatedMethodView):
    """Resource for record items."""

    view_name = "{0}_item"

    def __init__(
        self,
        read_permission_factory=None,
        update_permission_factory=None,
        delete_permission_factory=None,
        default_media_type=None,
        links_factory=None,
        loaders=None,
        search_class=None,
        indexer_class=None,
        **kwargs,
    ):
        """Constructor."""
        super().__init__(
            method_serializers={
                "DELETE": {
                    "*/*": lambda *args: make_response(*args),
                },
            },
            default_method_media_type={
                "GET": default_media_type,
                "PUT": default_media_type,
                "DELETE": "*/*",
                "PATCH": default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs,
        )
        self.search_class = search_class
        self.read_permission_factory = read_permission_factory
        self.update_permission_factory = update_permission_factory
        self.delete_permission_factory = delete_permission_factory
        self.links_factory = links_factory
        self.loaders = loaders or current_records_rest.loaders
        self.indexer_class = indexer_class

    @pass_record
    @need_record_permission("delete_permission_factory")
    def delete(self, pid, record, **kwargs):
        """Delete a record.

        Permissions: ``delete_permission_factory``

        Procedure description:

        #. The record is resolved reading the pid value from the url.

        #. The ETag is checked.

        #. The record is deleted.

        #. All PIDs are marked as DELETED.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        """
        self.check_etag(str(record.model.version_id))

        record.delete()
        # mark all PIDs as DELETED
        all_pids = PersistentIdentifier.query.filter(
            PersistentIdentifier.object_type == pid.object_type,
            PersistentIdentifier.object_uuid == pid.object_uuid,
        ).all()
        for rec_pid in all_pids:
            if not rec_pid.is_deleted():
                rec_pid.delete()
        db.session.commit()
        if self.indexer_class:
            self.indexer_class().delete(record)

        return "", 204

    @pass_record
    @need_record_permission("read_permission_factory")
    def get(self, pid, record, **kwargs):
        """Get a record.

        Permissions: ``read_permission_factory``

        Procedure description:

        #. The record is resolved reading the pid value from the url.

        #. The ETag and If-Modifed-Since is checked.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The requested record.
        """
        etag = str(record.revision_id)
        self.check_etag(str(record.revision_id))
        self.check_if_modified_since(record.updated, etag=etag)

        return self.make_response(pid, record, links_factory=self.links_factory)

    @require_content_types("application/json-patch+json")
    @pass_record
    @need_record_permission("update_permission_factory")
    def patch(self, pid, record, **kwargs):
        """Modify a record.

        Permissions: ``update_permission_factory``

        The data should be a JSON-patch, which will be applied to the record.
        Requires header ``Content-Type: application/json-patch+json``.

        Procedure description:

        #. The record is deserialized using the proper loader.

        #. The ETag is checked.

        #. The record is patched.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        self.check_etag(str(record.revision_id))
        try:
            record = record.patch(data)
        except (JsonPatchException, JsonPointerException):
            raise PatchJSONFailureRESTError()

        record.commit()
        db.session.commit()
        if self.indexer_class:
            self.indexer_class().index(record)

        return self.make_response(pid, record, links_factory=self.links_factory)

    @pass_record
    @need_record_permission("update_permission_factory")
    def put(self, pid, record, **kwargs):
        """Replace a record.

        Permissions: ``update_permission_factory``

        The body should be a JSON object, which will fully replace the current
        record metadata.

        Procedure description:

        #. The ETag is checked.

        #. The record is updated by calling the record API `clear()`,
           `update()` and then `commit()`.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        self.check_etag(str(record.revision_id))

        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()
        if self.indexer_class:
            self.indexer_class().index(record)
        return self.make_response(pid, record, links_factory=self.links_factory)


class SuggestResource(MethodView):
    """Resource for records suggests."""

    view_name = "{0}_suggest"

    def __init__(self, suggesters, search_class=None, **kwargs):
        """Constructor."""
        self.suggesters = suggesters
        self.search_class = search_class

    def get(self, **kwargs):
        """Get suggestions."""
        completions = []
        size = request.values.get("size", type=int)

        for k in self.suggesters.keys():
            val = request.values.get(k)
            if val:
                # Get completion suggestions
                opts = copy.deepcopy(self.suggesters[k])
                # Context suggester compatibility adjustment
                if "context" in opts.get("completion", {}):
                    context_key = "context"
                elif "contexts" in opts.get("completion", {}):
                    context_key = "contexts"
                else:
                    context_key = None

                if context_key:
                    ctx_field = opts["completion"][context_key]
                    ctx_val = request.values.get(ctx_field)
                    if not ctx_val:
                        raise SuggestMissingContextRESTError
                    opts["completion"][context_key] = {ctx_field: ctx_val}

                if size:
                    opts["completion"]["size"] = size

                completions.append((k, val, opts))

        if not completions:
            raise SuggestNoCompletionsRESTError(
                ", ".join(sorted(self.suggesters.keys()))
            )

        # Add completions
        s = self.search_class()
        for field, val, opts in completions:
            source = opts.pop("_source", None)
            if source is not None:
                s = s.source(source).suggest(field, val, **opts)
            else:
                s = s.suggest(field, val, **opts)

        response = s.execute().to_dict()["suggest"]

        result = dict()
        for field, val, opts in completions:
            result[field] = response[field]

        return make_response(jsonify(result))
