from OFS.ObjectManager import checkValidId
from zope.i18n import translate
from Products.CMFCore.utils import getToolByName
from plone.workflowmanager.utils import generate_id
from plone.workflowmanager import _


def not_empty(form, name):
    v = form.request.get(name, "").strip()
    if (
        v is None
        or (isinstance(v, str) and len(v) == 0)
        or (isinstance(v, (tuple, set, list)) and len(v) == 0)
    ):
        form.errors[name] = translate(
            _("This field is required."), context=form.request
        )
    return v


def id(form, name, container):
    elt_id = form.request.get(name, "").strip()
    putils = getToolByName(form.context, "plone_utils")
    elt_id = generate_id(putils.normalizeString(elt_id), container.objectIds())
    try:
        checkValidId(container, elt_id)
    except Exception:
        form.errors[name] = translate(
            _("Invalid name. Please try another."), context=form.request
        )
    return elt_id


def parse_set_value(form, key):
    val = form.request.get(key)
    if val:
        if isinstance(val, str):
            return set(val.split(","))
        elif isinstance(val, (tuple, list)):
            return set(val)
    return set()
