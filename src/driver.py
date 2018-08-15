from cloudshell.cp.core import DriverRequestParser
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.core.models import DriverResponse, DeployApp, DeployAppResult
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, ResourceCommandContext, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext, ResourceRemoteCommandContext

from cloudshell.core.logger import qs_logger
# from data_model import *  # run 'shellfoundry generate' to generate data model classes
from data_model import *
from heavenly_clouds_service import HeavenlyCloudsService
from heavenly_clouds_service_wrapper import HeavenlyCloudsServiceWrapper

import json


class HeavenlyCloudsShellDriver(ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.request_parser = DriverRequestParser()

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self.logger = qs_logger._create_logger(
            log_group='Heaven',
            log_category='Heavenly_Cloud',
            log_file_prefix='Heaven'
        )

        self.request_parser = DriverRequestParser()
        self.deployments = dict()
        self.request_parser.add_deployment_model(DeployAngelModel)
        self.request_parser.add_deployment_model(DeployManModel)

        # TODO
        # add custom deployment models to shellfoundry generate
        # fix or discuss on the fact that deployapp deployment path format is HeavenlyCloudsShell.HeavenlyCloudsAngelDeployment (why namespace?)
        self.deployments[DeployAngelModel.__deploymentModel__] = HeavenlyCloudsServiceWrapper.deploy_angel
        self.deployments[DeployManModel.__deploymentModel__] = HeavenlyCloudsServiceWrapper.deploy_man

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):

        # uncomment - if there is nothing to validate
        # return AutoLoadDetails([], [])

        # read from context
        resource = HeavenlyCloudsShell.create_from_context(context)

        self._log_value('get_inventory_context_json', context)

        # validating
        if resource.name == 'evil':
            raise ValueError('evil cannot use heaven ')

        if resource.region == 'sun':
            raise ValueError('invalid region, sorry ca\'nt deploy instances on the sun')

        # using your cloud provider sdk
        if not HeavenlyCloudsService.can_connect(resource.user, resource.password,
                                                 context.resource.address):  # TODO add address to resource (gal shellfoundry team)
            raise ValueError('could not connect using given credentials')

        # discovering - using your prefered custom cloud service you can discover and then update values
        if not resource.heaven_cloud_color:
            resource.heaven_cloud_color = HeavenlyCloudsService.get_prefered_cloud_color()

        return resource.create_autoload_details()

    # </editor-fold>

    # <editor-fold desc="Mandatory Commands">

    def Deploy(self, context, request=None, cancellation_context=None):
        """
       Deploy
       :param ResourceCommandContext context:
       :param str request: A JSON string with the list of requested deployment actions
       :param CancellationContext cancellation_context:
       :return:
       :rtype: str
       """

        self._log_value('deploy_request', request)
        self._log_value('deploy_context', context)

        # parse the json strings into action objects
        cloud_provider_resource = HeavenlyCloudsShell.create_from_context(context)
        actions = self.request_parser.convert_driver_request_to_actions(request)

        # extract DeployApp action
        deploy_action = single(actions, lambda x: isinstance(x, DeployApp))

        # if we have multiple supported deployment options use the 'deploymentPath' property
        # to decide which deployment option to use.
        deployment_name = deploy_action.actionParams.deployment.deploymentPath

        self._log_value('deployment_name', deployment_name)

        _my_deploy_method = self.deployments[deployment_name]
        deploy_result = _my_deploy_method(cloud_provider_resource, deploy_action, cancellation_context, self.logger)

        self._log_value('deploy_result', deploy_result)

        return DriverResponse([deploy_result]).to_driver_response_json()

    # def Deploy(self, context, request=None, cancellation_context=None):
    #     """
    #    Deploy
    #    :param ResourceCommandContext context:
    #    :param str request: A JSON string with the list of requested deployment actions
    #    :param CancellationContext cancellation_context:
    #    :return:
    #    :rtype: str
    #    """
    #
    #     # parse the json strings into action objects
    #     actions = self.request_parser.convert_driver_request_to_actions(request)
    #
    #     # extract DeployApp action
    #     deploy_action = single(actions, lambda x: isinstance(x, DeployApp))
    #
    #     # if we have multiple supported deployment options use the 'deploymentPath' property
    #     # to decide which deployment option to use.
    #     deployment_name = deploy_action.actionParams.deployment.deploymentPath
    #
    #     _my_deploy_method = self.deployments[deployment_name]
    #     deploy_result = _my_deploy_method(deploy_action, cancellation_context, self.logger)
    #
    #     return DriverResponse([deploy_result]).to_driver_response_json()
    #

    def PowerOn(self, context, ports):
        """
        Will power on the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        self._log_value('power_on_context', context)
        self._log_value('power_on_ports', ports)
        deployed_app_dict = json.loads(context.remote_endpoints[0].app_context.deployed_app_json)
        cloud_provider_resource = HeavenlyCloudsShell.create_from_context(context)

        HeavenlyCloudsServiceWrapper.power_on(cloud_provider_resource, deployed_app_dict['vmdetails']['uid'])

        pass

    def PowerOff(self, context, ports):
        """+
        Will power off the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def PowerCycle(self, context, ports, delay):
        pass

    def DeleteInstance(self, context, ports):
        """
        Will delete the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def GetVmDetails(self, context, requests, cancellation_context):
        """

        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """

        self._log_value('GetVmDetails_context', context)
        self._log_value('GetVmDetails_requests', requests)

        cloud_provider_resource = HeavenlyCloudsShell.create_from_context(context)
        result = HeavenlyCloudsServiceWrapper.get_vm_details(cloud_provider_resource, cancellation_context, requests)
        result_json = json.dumps(result, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

        self._log_value('GetVmDetails_result', result_json)

        return result_json

    def remote_refresh_ip(self, context, ports, cancellation_context):
        """
        Will update the address of the computer resource on the Deployed App resource in cloudshell
        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        pass

    # </editor-fold>

    ### NOTE: According to the Connectivity Type of your shell, remove the commands that are not
    ###       relevant from this file and from drivermetadata.xml.

    # <editor-fold desc="Mandatory Commands For L2 Connectivity Type">

    def ApplyConnectivityChanges(self, context, request):
        """
        Configures VLANs on multiple ports or port-channels
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON string with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the driver
        :rtype: str
        """
        pass

    # </editor-fold>

    # <editor-fold desc="Mandatory Commands For L3 Connectivity Type">

    def PrepareSandboxInfra(self, context, request, cancellation_context):
        """

        :param ResourceCommandContext context:
        :param str request:
        :param CancellationContext cancellation_context:
        :return:
        :rtype: str
        """
        '''
        # parse the json strings into action objects
        actions = self.request_parser.convert_driver_request_to_actions(request)

        action_results = _my_prepare_connectivity(context, actions, cancellation_context)

        return DriverResponse(action_results).to_driver_response_json()    
        '''
        pass

    def CleanupSandboxInfra(self, context, request):
        """

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """        '''
        # parse the json strings into action objects
        actions = self.request_parser.convert_driver_request_to_actions(request)

        action_results = _my_cleanup_connectivity(context, actions)

        return DriverResponse(action_results).to_driver_response_json()    
        '''
        pass

    # </editor-fold>

    # <editor-fold desc="Optional Commands For L3 Connectivity Type">

    def SetAppSecurityGroups(self, context, request):
        """

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files, etc.
        """
        pass

    # region helpers

    def _log_value(self, name, obj):

        if not obj:
            self.logger.info(name + 'Value  is None')

        if not self._is_primitive(obj):
            name = name + '__json_serialized'
            obj = json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

        self.logger.info(name)
        self.logger.info(obj)

    def _is_primitive(self, thing):
        primitive = (int, str, bool, float, unicode)
        return isinstance(thing, primitive)

    # endregion