# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
# from Products.DCWorkflow.Transitions import TRIGGER_AUTOMATIC, TRIGGER_USER_ACTION

# from plone.workflowmanager.browser.controlpanel import Base
# from plone.workflowmanager.utils import clone_transition
# from plone.workflowmanager.browser import validators
# from plone.workflowmanager.permissions import allowed_guard_permissions

# from plone.workflowmanager import WMMessageFactory as _
# import json


# class AddTransition(Base):
#     template = ViewPageTemplateFile("templates/add-new-transition.pt")
#     new_transition_template = ViewPageTemplateFile("templates/transition.pt")

#     def __call__(self):
#         self.errors = {}

#         if not self.request.get("form.actions.add", False):
#             return self.handle_response(tmpl=self.template)

#         self.authorize()
#         transition = validators.not_empty(self, "transition-name")
#         transition_id = validators.id(
#             self, "transition-name", self.selected_workflow.transitions
#         )

#         if not self.errors:
#             workflow = self.selected_workflow
#             workflow.transitions.addTransition(transition_id)
#             new_transition = workflow.transitions[transition_id]
#             clone_of_id = self.request.get("clone-from-transition")
#             new_transition.title = transition

#             if clone_of_id:
#                 clone_transition(new_transition, workflow.transitions[clone_of_id])
#             else:
#                 new_transition.actbox_name = transition
#                 new_transition.actbox_url = f"%(content_url)s/content_status_modify?workflow_action={transition_id}"
#                 new_transition.actbox_category = "workflow"
#                 new_transition.script_name = ""
#                 new_transition.after_script_name = ""

#             referenced_state = self.request.get("referenced-state")
#             if referenced_state:
#                 state = workflow.states[referenced_state]
#                 state.transitions += (new_transition.id,)

#             new_element = self.new_transition_template(transitions=[new_transition])
#             updates = {
#                 "objectId": new_transition.id,
#                 "element": new_element,
#                 "action": "add",
#                 "type": "transition",
#             }

#             return self.handle_response(
#                 message=_(
#                     "msg_transition_created",
#                     default='"${transition_id}" transition successfully created.',
#                     mapping={"transition_id": new_transition.id},
#                 ),
#                 graph_updates=updates,
#                 transition=new_transition,
#             )
#         return self.handle_response(tmpl=self.template, justdoerrors=True)


# class SaveTransition(Base):
#     transition_template = ViewPageTemplateFile("templates/transition.pt")

#     def update_guards(self):
#         wf = self.selected_workflow
#         transition = self.selected_transition
#         guard = transition.getGuard()

#         guard.permissions = tuple(
#             perm
#             for key, perm in allowed_guard_permissions(wf.getId()).items()
#             if f"transition-{transition.id}-guard-permission-{key}" in self.request
#         )

#         guard.roles = tuple(
#             validators.parse_set_value(self, f"transition-{transition.id}-guard-roles")
#             & set(wf.getAvailableRoles())
#         )

#         guard.groups = tuple(
#             validators.parse_set_value(self, f"transition-{transition.id}-guard-groups")
#             & set(g["id"] for g in self.getGroups())
#         )
#         transition.guard = guard

#     def update_transition_properties(self):
#         transition = self.selected_transition

#         transition.trigger_type = (
#             TRIGGER_AUTOMATIC
#             if f"transition-{transition.id}-autotrigger" in self.request
#             else TRIGGER_USER_ACTION
#         )

#         for attr in ["display-name", "new-state", "title", "description"]:
#             key = f"transition-{transition.id}-{attr}"
#             if key in self.request:
#                 setattr(transition, attr.replace("-", "_"), self.request[key])

#         for state in self.available_states:
#             key = f"transition-{transition.id}-state-{state.id}-selected"
#             if key in self.request:
#                 if transition.id not in state.transitions:
#                     state.transitions += (transition.id,)
#             elif transition.id in state.transitions:
#                 state.transitions = tuple(
#                     t for t in state.transitions if t != transition.id
#                 )

#     def __call__(self):
#         if form_data := self.request.get("form-box"):
#             self.request.update(json.loads(form_data))

#         self.authorize()
#         self.errors = {}

#         self.update_guards()
#         self.update_transition_properties()

#         element = self.transition_template(transitions=[self.selected_transition])
#         updates = {
#             "objectId": self.selected_transition.id,
#             "element": element,
#             "type": "transition",
#             "action": "update",
#         }

#         return self.handle_response(graph_updates=updates)


# class DeleteTransition(Base):
#     template = ViewPageTemplateFile("templates/delete-transition.pt")

#     def __call__(self):
#         self.errors = {}
#         transition = self.selected_transition
#         transition_id = transition.id

#         if self.request.get("form.actions.delete", False):
#             self.authorize()
#             self.actions.delete_rule_for(transition)
#             self.selected_workflow.transitions.deleteTransitions([transition_id])

#             for state in self.available_states:
#                 if transition_id in state.transitions:
#                     state.transitions = tuple(
#                         t for t in state.transitions if t != transition_id
#                     )

#             updates = {
#                 "objectId": transition_id,
#                 "action": "delete",
#                 "type": "transition",
#             }
#             return self.handle_response(
#                 message=_(
#                     "msg_transition_deleted",
#                     default='"${id}" transition has been successfully deleted.',
#                     mapping={"id": transition_id},
#                 ),
#                 graph_updates=updates,
#             )

#         if self.request.get("form.actions.cancel", False) == "Cancel":
#             return self.handle_response(
#                 message=_(
#                     "msg_deleting_canceled",
#                     default='Deleting the "${id}" transition has been canceled.',
#                     mapping={"id": transition_id},
#                 )
#             )
#         return self.handle_response(tmpl=self.template)


# class EditTransition(Base):
#     template = ViewPageTemplateFile("templates/workflow-transition.pt")

#     def __call__(self):
#         if not self.selected_workflow or not self.selected_transition:
#             return self.handle_response()

#         return self.render_transition_template(
#             self.selected_transition, self.available_states
#         )

#     def render_transition_template(self, transition, states):
#         return self.template(transition=transition, available_states=states)
