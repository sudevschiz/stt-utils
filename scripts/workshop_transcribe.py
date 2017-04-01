#!/usr/bin/env python
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#ADOPTED FROM :
#"""Google Cloud Speech API sample application using the REST API for batch
#processing.
#
#Example usage: python transcribe.py resources/audio.raw
#"""

# [START import_libraries]
import argparse
import base64
import json
import os
import csv

import googleapiclient.discovery
import httplib2
import time

from subprocess import check_output
# [END import_libraries]

# [START authenticating]
# Application default credentials provided by env variable
def get_speech_service():
    return googleapiclient.discovery.build('speech', 'v1beta1')
# [END authenticating]


def gc_async_transcribe(speech_uri):
    """Transcribe the given audio file asynchronously.

    Args:
        speech_uri: the name of the audio file in google bucket
    """
    service = get_speech_service()
    service_request = service.speech().asyncrecognize(
        body={
            'config': {
                # There are a bunch of config options you can specify. See
                # https://goo.gl/KPZn97 for the full list.
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                # See http://g.co/cloud/speech/docs/languages for a list of
                # supported languages.
                'languageCode': 'en-US',  # a BCP-47 language tag
            },
            'audio': {
                'uri': speech_uri
                }
            })
    # [END construct_request]
    # [START send_request]
    response = service_request.execute()
    print(json.dumps(response))
    # [END send_request]

    name = response['name']
    # Construct a GetOperation request.
    service_request = service.operations().get(name=name)

    while True:
        # Give the server a few seconds to process.
        print('Waiting for server processing...')
        time.sleep(60)
        # Get the long running operation with response.
        response = service_request.execute()
        if 'done' in response and response['done']:
            break
    response = response["response"]
    return(response)

def main():
    output = []
    with open("ResponsesFile_Workshop.csv","wb") as outfile, open("LongAudiofiles.txt","wb") as longFiles:
        writer = csv.writer(outfile)
        fieldnames = ['fileName', 'transcript']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        source_uri = "gs://datasphere-147517.appspot.com/mechanics_workshop/"
	try:
		filelist = check_output(["gsutil", "ls",source_uri])
	except Exception as e:
		print(e)
		return 0
	filelist = filelist.split("\n")

        #################

        CONFIDENCE_THRESHOLD = 0.5
        i=0
        SAMPLE_RATE = 8000

        for uri in filelist:
            if uri.endswith(".wav"):
                print(uri)
                try:
                    response = gc_async_transcribe(uri)
                except httplib2.ServerNotFoundError:
                    print("ServerNotFoundError : Please check the internet connection")
                    print("%d files converted. Exiting" % i)
                    break

                except googleapiclient.errors.HttpError as e:
                    print(str(e))
                    longFiles.write(uri)
                    #response = gc_async_transcribe(os.path.join(vm_dir,filename))

                #response = json.load(open("data.json","rb"))

                #print(json.dumps(response))
                if not bool(response):
                    writer.writerow({'fileName': uri, 'transcript': "NA"})
                    continue
                transcript = []
                for r in response['results']:
                    confidence = r['alternatives'][0]['confidence']
                    if(confidence > CONFIDENCE_THRESHOLD):
                        transcript.append(r['alternatives'][0]['transcript'])
                if not transcript:
                    transcript_full = "NA"
                transcript_full = "\n".join(transcript)
                writer.writerow({'fileName': uri, 'transcript': transcript_full})
                i = i +1
            else:
                continue
# [START run_application]
if __name__ == '__main__':
    main()
    # [END run_application]
