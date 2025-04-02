=====================
plone.workflowmanager
=====================

A PoC Backend add-on of Workflow Manager for Volto. For **Video Demo** and Frontend add-on see https://github.com/Faakhir30/volto-workflowmanager .

Features
--------
This addon enhances plone backend by following features:

- Migrated majority codebase of https://github.com/plone/plone.app.workflowmanager to python3 from python2.7 and plone6 from plone5.1.
- Rewrote codebase for restapi's instead of browser views with zcml interfaces.
- Added the following services:
   - AddWorkflowService: initializes a workflow, clones from a workflow
   - GetWorkflowsService: Gets all workflows including plone shipped ones
   - AddState: adds state to existing workflow
   - UpdateSecurityService: does recursiveUpdateRoleMappings for workflow
   - AssignWorkflowService: Assigns a workflow to some content-type
   - DeleteWorkflowService: Deletes a workflow
   - SanityCheckService: Checks for possible correctness of a workflow

Future Path
-----------

**As this is mere PoC, I haven't followed best plone.restapi practices**, so stopping this here, however, the next steps in this PoC would have been the following:

- Add/enahce new services:
 - EditState, DeleteState, EditTransition, DeleteTransition, CreateTransition, AssignWorkflow...
- Add Tests
- Add http examples for endpoints
- Add docs
- Configure Release process

Installation
------------
### For quick testing with [plonecli](https://github.com/plone/plonecli):
```
git clone https://github.com/Faakhir30/plone.workflowmanager
cd plone.workflowmanager
plonecli build serve
```

### For existing plone website (I've not tried, but hopefully would work):
Install plone.workflowmanager by adding it to your buildout::

    [buildout]

    ...

    eggs =
        plone.workflowmanager
    sources = 
        plone.workflowmanager = https://github.com/Faakhir30/plone.workflowmanager


and then running ``bin/buildout``
