from giza.action import Action

from action import inference

action_deploy = Action(entrypoint=inference, name="inference-local-action")
action_deploy.deploy(name="inference-action-deployment-k8", image="franalgaba/actions-examples:v0")