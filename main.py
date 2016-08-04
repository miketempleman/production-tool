
import argparse
import upload
import stopall
import botocore
import boto3
import time
from time import sleep

def appserversDown(wait=False, timeout=300):
    print("Checking that appservers are down. Waiting = %s, timeout=%d ", wait, timeout)
    filters = [{'Name':'tag:type', 'Values':['appserver']}]
    ec2 = boto3.client('ec2')
    count=0
    endtime = time.time() + timeout
    while True:
        reservations = ec2.describe_instances(Filters=filters)
        for reservation in reservations['Reservations']:
            for instance in reservation['Instances']:
                count += 1
        if count == 0:
            print("All appservers halted")
            return True
        elif not wait:
            print("Appservers not halted")
            return False
        elif time.time() > endtime:
            print('Timeout waiting for appsservers to die')
            return False
        print("Sleeping for 10 seconds")
        sleep(10)

    return False


def cleanupDB():
    print("Cleaning up the databse")
    if not appserversDown():
        ec2 = boto3.client('ec2')
        filters = [{'Name':'tag:type', 'Values':['mongos']}]
        reservations = ec2.describe_instances(Filters=filters)
        if len(reservations['Reservations']) > 0:
            client = boto3.client('ssm')
            result = client.send_command(InstanceIds=[reservations['Reservations'][0]['Instances'][0]['InstanceId']], DocumentName='CleanupTempCollections')
            if result['Command']['Status'] == 'Failed':
                raise botocore.exceptions.ClientError('Cleanup command faresuliled to execute')
            while True:
                cmd_result=client.list_command_invocations(CommandId=result['Command']['CommandId'], InstanceId=reservations['Reservations'][0]['Instances'][0]['InstanceId'])
                if cmd_result['CommandInvocations'][0]['Status'] == 'Success':
                    print("cleanup DB command completed")
                    break
                elif cmd_result['CommandInvocations'][0]['Status'] == 'Failed':
                    raise botocore.exceptions.ClientError('Cleanup command failed to execute')
                elif cmd_result['CommandInvocations'][0]['Status'] == 'TimedOut':
                    raise botocore.exceptions.ClientError('Cleanup command timed out during execution. Status unknown')
                elif cmd_result['CommandInvocations'][0]['Status'] == 'Cancelled':
                    raise botocore.exceptions.ClientError('Cleanup command was cancelled during execution.')
                sleep(10)

def main():
    global args
    try:
        if args.upload:
            upload.upload()
        if args.stopall:
            stopall.stopall()
        if args.rename:
            upload.rename()
        if args.cleanUp:
            cleanupDB()

        if args.restart:
            stopall.restart()

        if args.kitchenSink:
            upload.upload()
            stopall.stopall()
            upload.rename()
            stopall.restart()

        print("finished")

    except botocore.exceptions.ClientError as e:
        print(e)

class Args:
    pass

if __name__ == "__main__":
    args = Args()

    parser = argparse.ArgumentParser(description="Meshfire production server control tool")
    parser.add_argument('-sa', '--stopall', dest="stopall", action='store_true',
                        help='Stop all servers connected to production environment')
    parser.add_argument('-u', '--upload', dest="upload", action='store_true',
                        help="Upload production war to plover-upload in bucket plover")
    parser.add_argument('-rn', '--rename', dest="rename", action='store_true',
                        help="Rename plover-upload.war to plover.war in bucket plover")
    parser.add_argument('-rs', '--restart', dest="restart", action='store_true',
                        help="Restart stopped meshfire from existing plover.war")
    parser.add_argument('-ks', '--kitchenSink', dest="kitchenSink", action='store_true',
                        help="Push new war to plover-upload.war, stop all servers, restart meshfire from plover-upload.war ")
    parser.add_argument('-zc', '--zombieCheck', dest="zombieCheck", action='store_true',
                        help="Check for zombie appservers. if found, restart them")
    parser.add_argument('-cu', '--cleanUp', dest="cleanUp", action='store_true',
                        help="Run cleanup command on database. If any appservers are running halt this command")


    parser.parse_args(namespace=args)

    main()


