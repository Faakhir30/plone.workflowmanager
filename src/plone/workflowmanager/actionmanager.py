from zope.component import queryUtility

from plone.memoize import ram
from plone.contentrules.engine.interfaces import IRuleStorage, IRuleAssignmentManager
from plone.app.contentrules.conditions.wftransition import WorkflowTransitionCondition
from plone.contentrules.engine import utils
from plone.app.contentrules.rule import Rule, get_assignments
from plone.contentrules.engine.assignments import RuleAssignment
from Products.CMFCore.interfaces._events import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName
from plone.workflowmanager.utils import generateRuleName, generateRuleNameOld

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("plone")


class RuleAdapter:

    def __init__(self, rule, transition):
        self.rule = rule
        self.transition = transition

    @property
    @ram.cache(lambda *args: None)
    def portal(self):
        return getToolByName(self.transition, "portal_url").getPortalObject()

    def activate(self):
        """
        1) Make sure the condition is enabled for transition.
        2) Enable at root and bubble to item below.
        """
        c = WorkflowTransitionCondition()
        c.wf_transitions = [self.transition.id]
        self.rule.conditions = [c]
        self.rule.event = IActionSucceededEvent

        assignable = IRuleAssignmentManager(self.portal)
        path = "/".join(self.portal.getPhysicalPath())
        assignable[self.rule.__name__] = RuleAssignment(
            self.rule.id, enabled=True, bubbles=True
        )
        assignments = get_assignments(self.rule)
        if path not in assignments:
            assignments.insert(path)

    @property
    def id(self):
        return self.rule.id

    def get_action(self, index):
        return self.rule.actions[index]

    def action_index(self, action):
        return self.rule.actions.index(action)

    def action_url(self, action):
        return f"{self.portal.absolute_url()}/{self.rule.id}/++action++{self.action_index(action)}/edit"

    def delete_action(self, index):
        del self.rule.actions[index]

    @property
    def actions(self):
        return self.rule.actions


class ActionManager:

    def get_rule(self, transition):
        rulename = generateRuleName(transition)
        rulename_old = generateRuleNameOld(transition)
        if self.storage is not None:
            for rule in self.storage.values():
                if rule.__name__ in (rulename, rulename_old):
                    return RuleAdapter(rule, transition)
        return None

    def create(self, transition):
        rule = self.get_rule(transition)
        if rule is None:
            rule_id = generateRuleName(transition)
            r = Rule()
            r.title = _(f"{transition.id} transition content rule")
            r.description = _(
                "This content rule was automatically created "
                "by the workflow manager to create actions on "
                "workflow events. If you want the behavior to "
                "work as expected, do not modify this out of "
                "the workflow manager."
            )
            self.storage[rule_id] = r
            rule = RuleAdapter(r, transition)
            rule.activate()

        return rule

    @property
    @ram.cache(lambda *args: None)
    def storage(self):
        return queryUtility(IRuleStorage)

    @property
    @ram.cache(lambda *args: None)
    def available_actions(self):
        return utils.allAvailableActions(IActionSucceededEvent)

    def delete_rule_for(self, transition):
        rule = self.get_rule(transition)
        if rule is not None:
            del self.storage[rule.rule.__name__]
