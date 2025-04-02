from Products.CMFCore.utils import getToolByName
import json

from AccessControl import Unauthorized

from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName
from plone.memoize.view import memoize

# from plone.workflowmanager.browser.layout import GraphLayout
from plone.workflowmanager.permissions import (
    managed_permissions,
    allowed_guard_permissions,
)
from plone.workflowmanager.actionmanager import ActionManager
from plone.workflowmanager import _


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
