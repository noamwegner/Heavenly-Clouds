from data_model import HeavenResidentInstance,Cloud
import uuid

class HeavenlyCloudsService(object):

    @staticmethod
    def get_prefered_cloud_color():
        return 'pink'

    @staticmethod
    def can_connect(user, password, address):
        return True

    @staticmethod
    def allocate_resource():
        pass

    @staticmethod
    def do_other_stuff():
        pass

    @staticmethod
    def power_on():
        pass

    @staticmethod
    def create_man_instance(name, height, weight ,cloud_name,cloud_color):
        return HeavenResidentInstance(name, 'height {0} weight {1}'.format(height, weight ), Cloud(cloud_color, cloud_name, 0, 1),'8.8.4.4',str(uuid.uuid4()))
        pass

    @staticmethod
    def create_angel_instance(name, wings_count, flight_speed, cloud_name, cloud_color):
        return HeavenResidentInstance(name, 'wings count {0} flight speed {1}'.format(wings_count, flight_speed), Cloud(cloud_color, cloud_name, 0, 1),'8.8.8.8',str(uuid.uuid4()))
        pass

    @staticmethod
    def get_instance(cloud_provider_resource, name ,id,address):
        return HeavenResidentInstance(name, 'instance {0} {1}'.format(name ,id), Cloud('', '', 0, 1),address,str(id))