
import boto3
from time import sleep

def stopall():
    client = boto3.client('autoscaling')
    print("Stopping all app servers by shutting down desired capacity for all autoscaling groups")

    print("Setting MeshfireStreamServers group to 0 instances")
    response = client.set_desired_capacity(
        AutoScalingGroupName='MeshfireStreamServers',
        DesiredCapacity=0,
        HonorCooldown=False)

    print("Setting MeshfireDynamicAppServers group to 0 instances")
    response = client.set_desired_capacity(
        AutoScalingGroupName='MeshfireDynamicAppServers',
        DesiredCapacity=0,
        HonorCooldown=False)

    print("Setting MeshfireSchedAppServers group to 0 instances")
    response = client.set_desired_capacity(
        AutoScalingGroupName='MeshfireSchedAppServers',
        DesiredCapacity=0,
        HonorCooldown=False)

    print("Now watch the Plover-Alpha load balancer until all instances are shut down")
    elb = boto3.client('elb')
    running = True
    while running:
        sleep(5)
        result = elb.describe_instance_health(LoadBalancerName='Plover-Alpha')
        print ("%d appserver instances still running", len(result['InstanceStates']))
        running = len(result['InstanceStates']) > 0

    print("Appservers are all stopped. Now get to work!")

def restart():
    client = boto3.client('autoscaling')
    elb = boto3.client('elb')
    print("Restarting stream app servers. If any appservers are running this will generate an error")
    result = elb.describe_instance_health(LoadBalancerName='Plover-Alpha')
    if len(result['InstanceStates']) > 0:
        raise botocore.exceptions.ClientError('Appservers still running on load balancer. restart terminated')
    else:
        print("Setting MeshfireStreamServers group to 6 instances")
        response = client.set_desired_capacity(
        AutoScalingGroupName='MeshfireStreamServers',
        DesiredCapacity=6,
        HonorCooldown=False)



