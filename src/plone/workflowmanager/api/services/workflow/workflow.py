# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import IExpandableElement
from Products.CMFCore.interfaces._content import IWorkflowAware
from plone.restapi.services import Service
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from random import randint
from urllib.parse import urlencode
from plone.restapi.deserializer import json_body

from zope.publisher.interfaces import IPublishTraverse
from DateTime import DateTime
from plone.workflowmanager.graphviz import getGraph
from plone.workflowmanager import validators
from plone.workflowmanager import _

from urllib.parse import urlencode
import json

from Acquisition import aq_get
from AccessControl import Unauthorized

from zope.component import getUtility, getMultiAdapter
from zope.schema.interfaces import IVocabularyFactory
import zope.i18n

from Products.CMFCore.utils import getToolByName
from plone.memoize.view import memoize

# from plone.workflowmanager.browser.layout import GraphLayout
from plone.workflowmanager.permissions import (
    managed_permissions,
    allowed_guard_permissions,
)
from plone.workflowmanager.graphviz import HAS_GRAPHVIZ
from plone.workflowmanager.actionmanager import ActionManager
from plone.workflowmanager import _

from base64 import b64encode

plone_shipped_workflows = [
    "folder_workflow",
    "intranet_folder_workflow",
    "intranet_workflow",
    "one_state_workflow",
    "plone_workflow",
    "simple_publication_workflow",
    "comment_review_workflow",
]


class Base:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    debug = False
    errors = {}
    next_id = None  # the id of the next workflow to be viewed
    label = _("Workflow Manager")
    description = _("Manage your custom workflows TTW.")

    @property
    @memoize
    def managed_permissions(self):
        return managed_permissions(self.selected_workflow.getId())

    @property
    @memoize
    def actions(self):
        return ActionManager()

    @property
    @memoize
    def allowed_guard_permissions(self):
        return allowed_guard_permissions(self.selected_workflow.getId())

    @property
    @memoize
    def portal(self):
        utool = getToolByName(self.context, "portal_url")
        return utool.getPortalObject()

    @property
    @memoize
    def portal_workflow(self):
        return getToolByName(self.context, "portal_workflow")

    @property
    @memoize
    def available_workflows(self):
        return [w for w in self.workflows if w.id not in plone_shipped_workflows]

    @property
    @memoize
    def workflows(self):
        pw = self.portal_workflow
        ids = pw.portal_workflow.listWorkflows()
        return [pw[id] for id in sorted(ids)]

    @property
    @memoize
    def selected_workflow(self):
        selected = self.request.get("selected-workflow")
        if isinstance(selected, list) and selected:
            selected = selected[0]
        return (
            self.portal_workflow.get(selected)
            if selected in self.portal_workflow.objectIds()
            else None
        )

    @property
    @memoize
    def selected_state(self):
        state = self.request.get("selected-state")
        if isinstance(state, list) and state:
            state = state[0]
        return (
            self.selected_workflow.states.get(state) if self.selected_workflow else None
        )

    @property
    @memoize
    def selected_transition(self):
        transition = self.request.get("selected-transition")
        if isinstance(transition, list) and transition:
            transition = transition[0]
        return (
            self.selected_workflow.transitions.get(transition)
            if self.selected_workflow
            else None
        )

    @property
    @memoize
    def available_states(self):
        return (
            sorted(
                self.selected_workflow.states.objectValues(),
                key=lambda x: x.title.lower(),
            )
            if self.selected_workflow
            else []
        )

    @property
    @memoize
    def available_transitions(self):
        return (
            sorted(
                self.selected_workflow.transitions.objectValues(),
                key=lambda x: x.title.lower(),
            )
            if self.selected_workflow
            else []
        )

    def authorize(self):
        authenticator = getMultiAdapter(
            (self.context, self.request), name="authenticator"
        )
        if not authenticator.verify():
            raise Unauthorized

    def get_transition_paths(self, state=None):
        states = [state] if state else self.available_states
        paths = {}
        for state in states:
            stateId = state.id
            paths[stateId] = {
                trans.new_state_id: {trans.id: trans.title}
                for trans in map(self.get_transition, state.transitions)
                if trans and trans.new_state_id
            }
        return json.dumps(paths)

    # def get_graphLayout(self, workflow):
    #     gl = GraphLayout(self.context, self.request, workflow.id)
    #     return gl.getLayout()

    @property
    @memoize
    def next_url(self):
        return self.get_url()

    def get_url(
        self, relative=None, workflow=None, transition=None, state=None, **kwargs
    ):
        url = (
            f"{self.context.absolute_url()}/@@workflowmanager"
            if not relative
            else f"{self.context.absolute_url()}/{relative.lstrip('/')}"
        )
        params = {
            "selected-workflow": (
                workflow.id
                if workflow
                else (
                    self.next_id
                    or (self.selected_workflow.id if self.selected_workflow else None)
                )
            ),
            "selected-transition": transition.id if transition else None,
            "selected-state": state.id if state else None,
            **kwargs,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return f"{url}?{urlencode(params)}" if params else url

    @property
    @memoize
    def context_state(self):
        return getMultiAdapter((self.context, self.request), name="plone_portal_state")


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class DeleteWorkflow(Service):
    def __init__(self, context, request):
        self.request = json_body(request)
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        self.errors = {}

        # self.can_delete = len(self.assigned_types) == 0 # get assigned types to a workflow somehow

        # if not self.can_delete:
        #     return {"status": "error", "message": "Cant delete workflow unless assigned types removed and attached to some other workflow."}
        self.base.authorize()
        # delete all rules also.
        for transition in self.base.available_transitions:
            self.base.actions.delete_rule_for(transition)

        self.base.portal_workflow.manage_delObjects([self.base.selected_workflow.id])
        return {"status": "success", "message": "Workflow deleted successfully"}


@implementer(IPublishTraverse)
@adapter(IWorkflowAware, Interface)
class AddWorkflow(Service):
    def __init__(self, context, request):
        super().__init__(context, request)
        # Disable CSRF protection
        from zope.interface import alsoProvides
        import plone.protect.interfaces

        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        body = json_body(self.request)
        workflow = body.get("workflow-name")
        workflow_id = workflow.strip().replace("-", "_")
        if not workflow or not workflow_id:
            return {"error": "Missing required workflow information"}

        cloned_from_workflow = self.base.portal_workflow[
            body.get("clone-from-workflow")
        ]

        self.base.portal_workflow.manage_clone(cloned_from_workflow, workflow_id)
        new_workflow = self.base.portal_workflow[workflow_id]
        new_workflow.title = workflow

        return {
            "status": "success",
            "workflow_id": new_workflow.id,
            "message": _("Workflow created successfully"),
        }


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class UpdateSecuritySettings(Service):
    def __init__(self, context, request):
        self.request = json_body(request)
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        self.base.authorize()
        count = self.base.portal_workflow._recursiveUpdateRoleMappings(
            self.base.portal,
            {self.base.selected_workflow.id: self.base.selected_workflow},
        )
        return {
            "status": "success",
            "message": _(
                "msg_updated_objects",
                default="Updated ${count} objects.",
                mapping={"count": count},
            ),
        }


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class Assign(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        self.errors = {}

        self.base.authorize()
        params = urlencode(
            {
                "type_id": self.request.get("type_id"),
                "new_workflow": self.base.selected_workflow.id,
            }
        )
        return {
            "status": "success",
            "message": "Workflow assigned successfully",
            "redirect": self.context_state.portal_url()
            + "/@@content-controlpanel?"
            + params,
        }


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class SanityCheck(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        self.errors = {}
        states = self.base.available_states
        transitions = self.base.available_transitions
        self.errors["state-errors"] = []
        self.errors["transition-errors"] = []

        for state in states:
            found = False
            for transition in transitions:
                if transition.new_state_id == state.id:
                    found = True
                    break

            if (
                self.base.selected_workflow.initial_state == state.id
                and len(state.transitions) > 0
            ):
                found = True

            if not found:
                self.errors["state-errors"].append(state)

        for transition in transitions:
            found = False
            if not transition.new_state_id:
                found = True

            for state in states:
                if transition.id in state.transitions:
                    found = True
                    break

            if not found:
                self.errors["transition-errors"].append(transition)

        state_ids = [s.id for s in states]
        if (
            not self.base.selected_workflow.initial_state
            or self.base.selected_workflow.initial_state not in state_ids
        ):
            self.errors["initial-state-error"] = True

        has_errors = (
            len(self.errors["state-errors"]) > 0
            or len(self.errors["transition-errors"]) > 0
            or "initial-state-error" in self.errors
        )

        return {
            "status": "success" if not has_errors else "error",
            "errors": self.errors,
        }


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class Graph(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        # generate a random number to prevent browser from caching this...
        self.random_number = str(randint(0, 999999999))
        resp = self.request.response
        resp.setHeader("Content-Type", "image/gif")
        resp.setHeader("Last-Modified", DateTime().rfc822())
        graph = getGraph(self.base.selected_workflow)
        resp.setHeader("Content-Length", str(len(graph)))
        return graph


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class UpdateSecurityService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):

        workflow = self.get_selected_workflow()
        if not workflow:
            return {"error": "No workflow selected"}

        count = self.base.portal_workflow._recursiveUpdateRoleMappings(
            self.base.context, {workflow.id: workflow}
        )

        return {
            "status": "success",
            "count": count,
            "message": _(
                "msg_updated_objects",
                default="Updated ${count} objects.",
                mapping={"count": count},
            ),
        }

    def get_selected_workflow(self):
        workflow_id = self.request.get("selected-workflow")
        if workflow_id:
            return self.portal_workflow.get(workflow_id)
        return None


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class AssignWorkflowService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        workflow = self.get_selected_workflow()
        if not workflow:
            return {"error": "No workflow selected"}

        type_id = self.request.get("type_id")
        if not type_id:
            return {"error": "No content type specified"}

        # Update workflow chain for type
        chain = (workflow.id,)
        self.base.portal_workflow.setChainForPortalTypes((type_id,), chain)

        return {
            "status": "success",
            "workflow": workflow.id,
            "type": type_id,
            "message": _("Workflow assigned successfully"),
        }

    def get_selected_workflow(self):
        workflow_id = self.request.get("selected-workflow")
        if workflow_id:
            return self.base.portal_workflow.get(workflow_id)
        return None


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class DeleteWorkflowService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        workflow = self.get_selected_workflow()
        if not workflow:
            return {"error": "No workflow selected"}

        workflow_id = workflow.id
        self.base.portal_workflow.manage_delObjects([workflow_id])

        return {
            "status": "success",
            "workflow": workflow_id,
            "message": _("Workflow deleted successfully"),
        }

    def get_selected_workflow(self):
        body = json_body(self.request)
        workflow_id = body.get("selected-workflow")
        if workflow_id:
            return self.base.portal_workflow.get(workflow_id)
        return None


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class GraphService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        workflow = self.get_selected_workflow()
        if not workflow:
            return {"error": "No workflow selected"}

        try:
            graph_data = getGraph(workflow)
            if not graph_data:
                return {"error": "Could not generate graph"}
            print(graph_data, "graph_data>>>")
            # Convert graph binary data to base64 for JSON response
            encoded_graph = b64encode(graph_data).decode("utf-8")

            return {
                "status": "success",
                "workflow": workflow.id,
                "graph": {
                    "data": encoded_graph,
                    "content-type": "image/gif",
                    "encoding": "base64",
                },
            }
        except TypeError:
            return {"error": "Error generating workflow graph"}

    def get_selected_workflow(self):
        workflow_id = self.request.form.get("selected-workflow")
        if workflow_id:
            return self.base.portal_workflow.get(workflow_id)
        return None


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class SanityCheckService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        workflow = self.get_selected_workflow()
        if not workflow:
            return {"error": "No workflow selected"}

        states = workflow.states
        transitions = workflow.transitions
        errors = {
            "state_errors": [],
            "transition_errors": [],
            "initial_state_error": False,
        }

        # Check states
        for state in states.values():
            found = False
            for transition in transitions.values():
                if transition.new_state_id == state.id:
                    found = True
                    break

            if workflow.initial_state == state.id and len(state.transitions) > 0:
                found = True

            if not found:
                errors["state_errors"].append(
                    {
                        "id": state.id,
                        "title": state.title,
                        "error": "State is not reachable",
                    }
                )

        # Check transitions
        for transition in transitions.values():
            found = False
            if not transition.new_state_id:
                found = True

            for state in states.values():
                if transition.id in state.transitions:
                    found = True
                    break

            if not found:
                errors["transition_errors"].append(
                    {
                        "id": transition.id,
                        "title": transition.title,
                        "error": "Transition is not used by any state",
                    }
                )

        # Check initial state
        state_ids = [s.id for s in states.values()]
        if not workflow.initial_state or workflow.initial_state not in state_ids:
            errors["initial_state_error"] = True

        has_errors = (
            len(errors["state_errors"]) > 0
            or len(errors["transition_errors"]) > 0
            or errors["initial_state_error"]
        )

        return {
            "status": "success" if not has_errors else "error",
            "workflow": workflow.id,
            "errors": errors,
            "message": _("Workflow validation complete"),
        }

    def get_selected_workflow(self):
        workflow_id = self.request.get("selected-workflow")
        if workflow_id:
            return self.base.portal_workflow.get(workflow_id)
        return None


@implementer(IExpandableElement)
@adapter(IWorkflowAware, Interface)
class GetWorkflowsService(Service):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        portal_workflow = self.base.portal_workflow
        workflows = []

        for workflow_id in portal_workflow.listWorkflows():
            workflow = portal_workflow[workflow_id]

            # Skip Plone shipped workflows if needed
            if workflow_id in plone_shipped_workflows:
                continue

            workflow_info = {
                "id": workflow_id,
                "title": workflow.title or workflow_id,
                "description": getattr(workflow, "description", ""),
                "initial_state": workflow.initial_state,
                "states": [
                    {
                        "id": state_id,
                        "title": state.title,
                        "transitions": state.transitions,
                    }
                    for state_id, state in workflow.states.items()
                ],
                "transitions": [
                    {
                        "id": trans_id,
                        "title": trans.title,
                        "new_state": trans.new_state_id,
                        "description": getattr(trans, "description", ""),
                    }
                    for trans_id, trans in workflow.transitions.items()
                ],
            }

            # Get content types using this workflow
            chain_types = []
            for portal_type, chain in self.base.portal_workflow.listChainOverrides():
                if workflow_id in chain:
                    chain_types.append(portal_type)

            workflow_info["assigned_types"] = chain_types
            workflows.append(workflow_info)

        return {"workflows": workflows}
