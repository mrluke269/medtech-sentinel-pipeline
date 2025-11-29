# S3 Bucket Setup

## Create the bucket
```powershell
aws s3 mb s3://medtech-sentinel-raw-luke --region us-east-2
```

## Verify bucket created
```powershell
aws s3 ls
```

## Create folder structure
```powershell
echo "placeholder" > placeholder.txt
aws s3 cp placeholder.txt s3://medtech-sentinel-raw-luke/data/heart-valves/placeholder.txt
aws s3 cp placeholder.txt s3://medtech-sentinel-raw-luke/data/pulse-oximeters/placeholder.txt
del placeholder.txt
```

## Verify structure
```powershell
aws s3 ls s3://medtech-sentinel-raw-luke --recursive
```

