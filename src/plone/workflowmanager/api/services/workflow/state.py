from persistent.mapping import PersistentMapping
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from Products.CMFCore.interfaces._content import IWorkflowAware
from zope.component import adapter
from zope.interface import Interface

from plone.workflowmanager.utils import clone_state

from plone.workflowmanager.browser import validators
from plone.workflowmanager.permissions import managed_permissions
from plone.workflowmanager.api.services.workflow.base import Base
from plone.workflowmanager import _


@adapter(IWorkflowAware, Interface)
class AddState(Service):
    def __init__(self, context, request):
        self.request = request
        self.payload = json_body(request)
        self.context = context
        self.base = Base(context, request)

    def reply(self):
        self.errors = {}

        self.base.authorize()
        state = validators.not_empty(self, "state-name")
        state_id = validators.id(self, "state-name", self.selected_workflow.states)

        if self.errors:
            return {"status": "error", "message": self.errors}
        wf = self.base.selected_workflow
        wf.states.addState(state_id)
        new_state = wf.states[state_id]
        clone_of_id = self.payload.get("clone-from-state")
        if clone_of_id:
            clone_state(new_state, wf.states[clone_of_id])

        new_state.title = state
        referenced_transition = self.payload.get("referenced-transition", None)
        if referenced_transition:
            new_state.transitions += (referenced_transition,)

        msg = _(
            "msg_state_created",
            default=f'"{new_state.id}" state successfully created.',
            mapping={"state_id": new_state.id},
        )

        return {"status": "success", "message": msg, "state": new_state}


# class DeleteState(Base):
#     template = ViewPageTemplateFile("templates/delete-state.pt")

#     def __call__(self):
#         self.errors = {}
#         state = self.selected_state
#         transitions = self.available_transitions
#         state_id = state.id

#         self.is_using_state = any(
#             transition.new_state_id == state_id for transition in transitions
#         )

#         if self.request.get("form.actions.delete", False):
#             self.authorize()
#             replacement = None

#             if self.is_using_state:
#                 replacement = self.request.get(
#                     "replacement-state", self.available_states[0].id
#                 )
#                 for transition in self.available_transitions:
#                     if state_id == transition.new_state_id:
#                         transition.new_state_id = replacement

#                 chains = self.portal_workflow.listChainOverrides()
#                 types_ids = [c[0] for c in chains if self.selected_workflow.id in c[1]]
#                 remap_workflow(
#                     self.context,
#                     types_ids,
#                     (self.selected_workflow.id,),
#                     {state_id: replacement},
#                 )

#             self.selected_workflow.states.deleteStates([state_id])
#             updates = {"objectId": state_id, "action": "delete", "type": "state"}
#             if replacement:
#                 updates["replacement"] = replacement

#             return self.handle_response(
#                 message=_(
#                     "msg_state_deleted",
#                     default=f'"{state_id}" state has been successfully deleted.',
#                     mapping={"id": state_id},
#                 ),
#                 graph_updates=updates,
#             )
#         elif self.request.get("form.actions.cancel", False) == "Cancel":
#             return self.handle_response(
#                 message=_(
#                     "msg_state_deletion_canceled",
#                     default=f'Deleting the "{state_id}" state has been canceled.',
#                     mapping={"id": state_id},
#                 )
#             )
#         else:
#             return self.handle_response(tmpl=self.template)


# class SaveState(Base):
#     updated_state_template = ViewPageTemplateFile("templates/state.pt")

#     def update_selected_transitions(self):
#         wf = self.selected_workflow
#         state = wf.states[self.request.get("selected-state")]
#         transitions = wf.transitions.objectIds()
#         state.transitions = tuple(
#             t for t in transitions if f"transition-{t}-state-{state.id}" in self.request
#         )

#     def __call__(self):
#         if self.request.get("form-box"):
#             form_data = json.loads(self.request.get("form-box"))
#             self.request.update(form_data)

#         self.authorize()
#         self.errors = {}
#         wf = self.selected_workflow
#         state = wf.states[self.request.get("selected-state")]

#         old_transitions = set(state.transitions)
#         self.update_selected_transitions()
#         new_transitions = set(state.transitions)

#         updated_state = self.updated_state_template(states=[state])
#         updates = {
#             "objectId": state.id,
#             "action": "update",
#             "type": "state",
#             "element": updated_state,
#             "add": list(new_transitions - old_transitions),
#             "remove": list(old_transitions - new_transitions),
#         }

#         return self.handle_response(graph_updates=updates)


# class EditState(Base):
#     template = ViewPageTemplateFile("templates/workflow-state.pt")

#     def __call__(self):
#         wf = self.selected_workflow
#         if not wf:
#             return self.handle_response()

#         state = self.selected_state
#         if not state:
#             return self.handle_response()

#         return self.render_state_template(state, self.available_transitions)

#     def render_state_template(self, state, transitions):
#         return self.template(state=state, available_transitions=transitions)
