# EMR on EKS
This was a learning experiment. This is not a tutorial.

### Prerequisites
* kubectl
* eksctl
* awscli

### Create an EKS cluster
NOTE: I did this in the AWS Console. Created a small node group for core k8s services
and a larger node group that would be my actual compute nodes. Why doesn't AWS let you
have zero nodes in a node group? What if I don't need an m5.12xlarge running all the time?

### Configure `kubectl` to the EKS cluster
    aws eks update-kubeconfig \
    --region us-east-1 \
    --name eks-emr

### Test `kubectl`
    kubectl get svc

### Enable k8s dashboard
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.5/aio/deploy/recommended.yaml

### Enable dashboard admin access
Follow this guide: https://docs.aws.amazon.com/eks/latest/userguide/dashboard-tutorial.html

### Create a k8s namespace - one per EMR virtual cluster
    kubectl create namespace eks-emr-ns

### Create IAM identity mapping (one per namespace)
    eksctl create iamidentitymapping \
    --cluster eks-emr \
    --namespace eks-emr-ns \
    --service-name "emr-containers"

### Allow nodes in your EKS cluster to assume the EMR job execution role
    aws emr-containers update-role-trust-policy \
       --cluster-name eks-emr \
       --namespace eks-emr-ns \
       --role-name eks-emr-job-execution-role

### Create a virtual EMR cluster
    aws emr-containers create-virtual-cluster \
    --name virtual_cluster_name \
    --container-provider '{
        "id": "eks-emr",
        "type": "EKS",
        "info": {
            "eksInfo": {
                "namespace": "eks-emr-ns"
            }
        }
    }'

### Enable cluster autoscaling
https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html

I don't think I ever really got this part working.

### Enable OIDC provider for `eksctl`
    eksctl utils associate-iam-oidc-provider --region=us-east-1 --cluster=eks-emr --approve

I don't really know the details of this, but it's some sort of authentication provider.

### Run SparkPi
    aws emr-containers start-job-run \
      --virtual-cluster-id somethingsomething \
      --name SparkPi \
      --execution-role-arn arn:aws:iam::12345678901:role/eks-emr-job-execution-role \
      --release-label emr-6.2.0-latest \
      --job-driver '{"sparkSubmitJobDriver": {"entryPoint": "local:///usr/lib/spark/examples/src/main/python/pi.py","sparkSubmitParameters": "--conf spark.executor.instances=2 --conf spark.executor.memory=2G --conf spark.executor.cores=2 --conf spark.driver.cores=1"}}' \
      --configuration-overrides '{"monitoringConfiguration": {"cloudWatchMonitoringConfiguration": {"logGroupName": "log_group_name", "logStreamNamePrefix": "log_stream_prefix"}}}'

## How this works
1. Set up an EKS cluster. Add a core node group for k8s services. Add a second node group for EMR jobs (e.g. m5.xlarge).
2. Greate a namespace per cluster (I think).
3. Create an IAM Identity mapping from a cluster to a namespace.
4. One time creation of an EMR job execution role.
5. Allow the EKS cluster's nodes to assume the job execution role.
6. Create a virtual EMR cluster on top of EKS (given a namespace and EKS cluster ID)
7. Run jobs?!

## TODO
NOTE: I don't actually plan on doing this, but these are good next steps.

1. Where are the logs? they didn't show up in CloudWatch for me.
2. How do you stop a job that's running?
3. How to specify a docker image with my code/dependencies in it

## Thoughts
1. EMR on EKS is extremely alpha quality. There is no UI for it. It's not production-ready. You need to submit jobs using the AWS CLI.
2. What exactly is the purpose of EMR on EKS? It lets you submit jobs to an EKS cluster using AWS-provided Docker images
that have Spark - but why not just skip EMR altogether and make your own Docker images (you'll need to do this anyway if you want any pip packages...?)
3. EKS does not have cluster autoscaling enabled by default so it was fun learning how to set that up. I'm sure even sure I got it working, I gave up after 30 minutes
of EKS/EC2 trying to figure out how to add nodes to my EKS cluster.
4. It seems to take 5-15 minutes to add a node to the EKS cluster. You could spin up a regular EMR cluster in roughly the same amount of time.
5. EMR on EKS pricing - I can't believe it's not free. You pay for EKS, EC2/Fargate, EBS/S3, and EMR, even though EKS is doing the orchestration.
6. I expected EMR on EKS to do more in terms of managing EKS for me.
7. If I'm a data scientist, I don't want to manage an EKS/k8s cluster. I just want autoscaling and not to have to wait for EMR to spin up for 10 minutes.
8. Since there were many manual k8s/kubectl steps, I'm sure this whole guide will break in a year or two as new versions of everything change things.
9. Performing pretty much any action in EKS has a lag of 1-2 minutes before changes take effect. Adding nodes takes 5 minutes which is a lot longer than expected. (Lambda function warmup time is what, 30-60 seconds in the absolute worst case?)

## Resources
1. https://www.youtube.com/watch?v=ANq4g01iLMM - pretty good tutorial video
2. https://aws.amazon.com/emr/pricing/ - EMR on EKS pricing
