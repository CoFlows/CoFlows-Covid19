cd ..
docker run --rm -v $(pwd):/app/mnt --env "config_file=$1" coflows/ce cloud deploy