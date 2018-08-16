import uuid
import datetime
import os
from cloudshell.cp.core.models import *
from data_model import *
from heavenly_clouds_service import HeavenlyCloudsService


import json

class HeavenlyCloudsServiceWrapper(object):

    @staticmethod
    def deploy_angel(cloud_provider_resource,deploy_app_action, cancellation_context, logger):

        if cancellation_context.is_cancelled:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        # deployment_model type : DeployAngelModel
        deployment_model = deploy_app_action.actionParams.deployment.customModel

        # generate unique name to avoid name collisions
        machine_unique_name = deploy_app_action.actionParams.appName + '__' + str(uuid.uuid4())[:6]

        # actually creating the instance
        vm_instance = HeavenlyCloudsService.create_angel_instance(cloud_provider_resource,machine_unique_name,
                                                                  deployment_model.wings_count,
                                                                  deployment_model.flight_speed,
                                                                  deployment_model.cloud_size,
                                                                  deployment_model.cloud_image_id)

        # Creating VmDetailsData from instance
        vm_details_data = HeavenlyCloudsServiceWrapper.extract_vm_details(vm_instance)

        # result must include the action id it results for, so server can match result to action
        action_id = deploy_app_action.actionId

        # optional
        # deployed_app_attributes contains the attributes on the deployed app
        # use to override attributes default values
        deployed_app_attributes = []
        deployed_app_attributes.append(Attribute('Password',HeavenlyCloudsService.create_new_password(vm_instance)))
        deployed_app_attributes.append(Attribute('User', 'super_user'))

        # optional
        # deployed_app_attributes can contain dynamic data on the deployed app
        # similar to AWS tagsimport datetime
        deployed_app_additional_data_dict = {'create date': datetime.datetime.now().isoformat() , 'created by' : str(os.path.abspath(__file__))}

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=machine_unique_name,
                               deployedAppAddress=vm_instance.private_ip, deployedAppAttributes=deployed_app_attributes,
                               deployedAppAdditionalData=deployed_app_additional_data_dict,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def deploy_man(cloud_provider_resource,deploy_app_action, cancellation_context, logger):

        if cancellation_context.is_cancelled:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        deployment_model = deploy_app_action.actionParams.deployment.customModel

        # generate unique name to avoid name collisions
        machine_unique_name = deploy_app_action.actionParams.appName + '__' + str(uuid.uuid4())[:6]

        # actually creating the instance
        vm_instance = HeavenlyCloudsService.create_man_instance(cloud_provider_resource,machine_unique_name,
                                                                  deployment_model.weight,
                                                                  deployment_model.height,
                                                                  deployment_model.cloud_size,
                                                                  deployment_model.cloud_image_id)
        # Creating VmDetailsData from instance
        vm_details_data = HeavenlyCloudsServiceWrapper.extract_vm_details(vm_instance)

        # result must include the action id it results for, so server can match result to action
        action_id = deploy_app_action.actionId

        # optional
        # deployed_app_attributes contains the attributes on the deployed app
        # use to override attributes default values
        deployed_app_attributes = []
        deployed_app_attributes.append(Attribute('Password', HeavenlyCloudsService.create_new_password(vm_instance)))
        deployed_app_attributes.append(Attribute('User', 'super_user'))

        # optional
        # deployed_app_attributes can contain dynamic data on the deployed app
        # similar to AWS tagsimport datetime
        deployed_app_additional_data_dict = {'create date': datetime.datetime.now().isoformat(),
                                             'created by': str(os.path.abspath(__file__))}

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=machine_unique_name,
                               deployedAppAddress=vm_instance.private_ip, deployedAppAttributes=deployed_app_attributes,
                               deployedAppAdditionalData=deployed_app_additional_data_dict,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def extract_vm_details(vm_instance):
        vm_instance_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_data(vm_instance)
        vm_network_data =  HeavenlyCloudsServiceWrapper.extract_vm_instance_network_data(vm_instance)

        return VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data)


    @staticmethod
    def extract_vm_instance_data(instance):

        data = [
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
                VmDetailsProperty(key='Device Index', value=str(i)),
                VmDetailsProperty(key='MAC Address', value=str(uuid.uuid4())),
                VmDetailsProperty(key='Speed', value='1KB'),
            ]

            current_interface = VmDetailsNetworkInterface(interfaceId=i, networkId=i,
                                                          isPrimary=i == 0,  # specifies whether nic is the primary interface
                                                          isPredefined=False, # specifies whether network existed before reservation
                                                          networkData=network_data,
                                                          privateIpAddress='10.0.0.' + str(i),
                                                          publicIpAddress='8.8.8.' + str(i))
            network_interfaces.append(current_interface)

        return network_interfaces

    @staticmethod
    def get_vm_details(cloud_provider_resource, cancellation_context, requests_json):

        requests = json.loads(requests_json)

        results = []

        for request in requests[u'items']:

            if cancellation_context.is_cancelled:
                break

            vm_name = request[u'deployedAppJson'][u'name']
            vm_uid =  request[u'deployedAppJson'][u'vmdetails'][u'uid']
            address = request[u'deployedAppJson'][u'address']
            vm_instance = HeavenlyCloudsService.get_instance(cloud_provider_resource, vm_name, vm_uid, address)

            vm_instance_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_data(vm_instance)
            vm_network_data = HeavenlyCloudsServiceWrapper.extract_vm_instance_network_data(vm_instance)

            # TODO when prepare connectivity is finished uncomment
            # currently we get error: Check failed because resource is connected to more than one subnet, while reservation doesn't have any subnet services
            # result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data, appName=vm_name)
            result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=None, appName=vm_name)
            results.append(result)

        return results

    @staticmethod
    def power_on(cloud_provider_resource, vm_id):
        HeavenlyCloudsService.power_on(cloud_provider_resource,vm_id)

