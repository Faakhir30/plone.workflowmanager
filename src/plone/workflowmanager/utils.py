from Products.DCWorkflow.Guard import Guard


def generate_id(org_id, ids):
    count = 1
    new_id = org_id
    while new_id in ids:
        new_id = f"{org_id}-{count}"
        count += 1
    return new_id


def clone_transition(transition, clone):
    transition.description = clone.description
    transition.new_state_id = clone.new_state_id
    transition.trigger_type = clone.trigger_type

    if clone.guard:
        guard = Guard()
        guard.permissions = list(clone.guard.permissions)
        guard.roles = list(clone.guard.roles)
        guard.groups = list(clone.guard.groups)
        transition.guard = guard

    transition.actbox_name = transition.title
    transition.actbox_url = clone.actbox_url.replace(clone.id, transition.id)
    transition.actbox_category = clone.actbox_category
    transition.var_exprs = clone.var_exprs
    transition.script_name = clone.script_name
    transition.after_script_name = clone.after_script_name


def clone_state(state, clone):
    state.transitions = list(clone.transitions)
    state.permission_roles = (
        clone.permission_roles.copy() if clone.permission_roles else None
    )
    state.group_roles = clone.group_roles.copy() if clone.group_roles else None
    state.var_values = clone.var_values.copy() if clone.var_values else None
    state.description = clone.description


def generateRuleName(transition):
    return f"--workflowmanager--{transition.getWorkflow().id}--{transition.id}"


def generateRuleNameOld(transition):
    return f"--workflowmanager--{transition.id}"
