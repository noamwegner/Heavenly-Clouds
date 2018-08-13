from cloudshell.cp.core.models import *
from data_model import *
from heavenly_clouds_service import HeavenlyCloudsService


import json

class HeavenlyCloudsServiceWrapper(object):

    @staticmethod
    def deploy_angel(deploy_app_action, cancellation_context, logger):

        logger.error('in deploy_angel')
        if cancellation_context.is_cancelled:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        deployment_model = deploy_app_action.actionParams.deployment.customModel

        deployment_model_json = json.dumps(deployment_model, default=lambda o: o.__dict__,
                                  sort_keys=True, indent=4)

        logger.error('deployment_model_json')
        logger.error(deployment_model_json)

        # do real stuff
        vm_instance = HeavenlyCloudsService.create_angel_instance(deploy_app_action.actionParams.appName,
                                                                  deployment_model.wings_count,
                                                                  deployment_model.flight_speed,
                                                                  deployment_model.cloud_name,
                                                                  deployment_model.cloud_color)

        vm_instance_json = json.dumps(vm_instance, default=lambda o: o.__dict__,
                                           sort_keys=True, indent=4)

        logger.error('vm_instance_json')
        logger.error(vm_instance_json)

        vm_details_data = HeavenlyCloudsServiceWrapper.extract_vm_details(vm_instance)

        #public_ip_attr = Attribute('Public IP', vm_instance.ip)
        cloud_ix_attr = Attribute('Cloud Index', vm_instance.cloud.index)
        deployed_app_attributes = [cloud_ix_attr]

        # result must include the action id it results for
        action_id = deploy_app_action.actionId

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=vm_instance.name,
                               deployedAppAddress=vm_instance.ip, deployedAppAttributes=deployed_app_attributes,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def deploy_man( deploy_app_action, cancellation_context, logger):

        logger.error('in deploy_man')

        if cancellation_context.is_cancelled:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        deployment_model = deploy_app_action.actionParams.deployment.customModel

        if isinstance(deployment_model,DeployManModel):
            pass

        # do real stuff
        vm_instance = HeavenlyCloudsService.create_man_instance(deploy_app_action.actionParams.appName,
                                                                  deployment_model.weight,
                                                                  deployment_model.height,
                                                                  deployment_model.cloud_name,
                                                                  deployment_model.cloud_color)

        vm_details_data = HeavenlyCloudsServiceWrapper.extract_vm_details(vm_instance)

        #public_ip_attr = Attribute('Public IP', vm_instance.ip)
        cloud_ix_attr = Attribute('Cloud Index', vm_instance.cloud.index)
        deployed_app_attributes = [cloud_ix_attr]

        # result must include the action id it results for
        action_id = deploy_app_action.actionId

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=vm_instance.name,
                               deployedAppAddress=vm_instance.ip, deployedAppAttributes=deployed_app_attributes,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def extract_vm_details(vm_instance):
        vm_instance_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_data(vm_instance)
        vm_network_data =  HeavenlyCloudsServiceWrapper.extract_vm_instance_network_data(vm_instance)

        return VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data)


    @staticmethod
    def extract_vm_instance_data(instance):

        data = [
            VmDetailsProperty(key='Cloud Name', value='cloud 9' if not instance else instance.cloud.name),
            VmDetailsProperty(key='Cloud Index', value='0'),
            VmDetailsProperty(key='Cloud Size', value='not so big'),
            VmDetailsProperty(key='Instance Name', value='dummy' if not instance else instance.name),
            VmDetailsProperty(key='Hidden stuff', value='something not for UI',hidden=True),
        ]

        return data

    @staticmethod
    def extract_vm_instance_network_data(instance):

        network_interfaces = []

        # for each network interface
        for i in range(2):
            network_data = [
                VmDetailsProperty(key='MaxSpeed', value='1KB'),
                VmDetailsProperty(key='Network Type', value='Ethernet'),
            ]

            current_interface = VmDetailsNetworkInterface(interfaceId=i, networkId=i,
                                                          isPrimary=i == 0,  # if nic is the primary interface
                                                          isPredefined=False,
                                                          # if the network existed before reservation



                                                          networkData=network_data,
                                                          privateIpAddress='10.0.0.' + str(i),
                                                          publicIpAddress='8.8.8.' + str(i))
            network_interfaces.append(current_interface)

        return network_interfaces

    @staticmethod
    def get_vm_details(command_context, cancellation_context, requests_json):


        resource = HeavenlyCloudsShell.create_from_context(command_context)
        requests = DeployDataHolder(json.loads(requests_json)).items
        results = []

        for request in requests:

            if cancellation_context.is_cancelled:
                break

            vm_name = request.deployedAppJson.name
            vm_uid = request.deployedAppJson.vmdetails.uid
            address = request.deployedAppJson.address

            vm_instance = HeavenlyCloudsService.get_instance(resource,vm_name,vm_uid,address)

            vm_instance_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_data(vm_instance)
            vm_network_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_network_data(vm_instance)

            # TODO when prepare connectivity is finished uncomment
            # currently we get error: Check failed because resource is connected to more than one subnet, while reservation doesn't have any subnet services
            # result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data, appName=vm_name)
            result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=None, appName=vm_name)
            results.append(result)

        return results

