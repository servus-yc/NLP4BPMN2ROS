﻿import numpy as np
import re
import openai
import json
from xml.dom import minidom
from config import key 
from BPMN.BPMN_dict import BPMNdict
from BPMN.pre_functions import dictionary, readXmlFile
from GPT3.NLP_functions import nlp_classification_results, corr_label 
from ROS.writeROS_function import substitute
"""
We will try to integrate all the functions in this one function later
"""

# initialization
openai.api_key = key  # enter your API for GPT-3 in the config file 


# name of the file - activate the file by switching to filename1
filename1 = "UC1_CS_Clip_Lightbarrier2LightbarrierHolder.bpmn"
filename1 ="UC1_CS_Clip_BasePlate2MotorAssembly2.bpmn" #works fine
filename1= "UC1_CS_Clip_Motor2MotorAssembly0.bpmn" #works fine
filename1 = "UC1_CS_Clip_MotorGear2MotorAssembly1.bpmn" #works fine
filename1="UC1_CS_PickAndPlace_Baseplate.bpmn" #works fine
filename1 = "UC1_CS_Clip_Lightbarrier2LightbarrierHolder.bpmn"
filename1 = "UC1_CS_Clip_TransmissionGear2MotorHolder.bpmn" #ok after Uppercase 
print(filename1)
def main():
    """
    1. exact the text in BPMN
    2. get the primitive command by GPT-3 classification
    3. output robot's programming code in ROS
    """
    # 1. exact the text in BPMN
    # reads the XML file for the BPMN diagram specified in files.py
    file = readXmlFile(filename1)

    # definitions of tags to be extracted from the XML file
    activities = file.getElementsByTagName('bpmn:serviceTask')
    lane = file.getElementsByTagName('bpmn:lane')
    objRef = file.getElementsByTagName(
        'bpmn:dataObjectReference')  # uses the id  attribute to find the tag and extract the name of element from it

    actRefArr = []
    actObjArr = []

    for i in lane:
        if (i.attributes['name'].value.lower() == "robot"):  # robot lane
            if activities:
                for activity in activities:
                    association = activity.getElementsByTagName("bpmn:dataInputAssociation")
                    if association:
                        for sourceRef in association:
                            
                            #add spacing between uppercase words if no spacing provided
                            activity_modified =re.sub(r'(?P<end>[a-z])(?P<start>[A-Z])', '\g<end> \g<start>', activity.attributes['name'].value)
                            
                            actRefArr.append(
                                [activity.attributes['id'].value.lower(), activity_modified.lower(),
                                 sourceRef.getElementsByTagName("bpmn:sourceRef")[0].firstChild.nodeValue,
                                 'obj_placeholder'])
                    else:
                        actRefArr.append(
                            [activity.attributes['id'].value.lower(), activity.attributes['name'].value.lower(), 'None',
                             'None'])

    objNameIdPairs = {k.attributes['id'].value: k.attributes['name'].value.lower() for k in objRef}
    actObjFullArr = []
    for p in actRefArr:
        if p[2] in objNameIdPairs.keys():
            p[3] = objNameIdPairs[p[2]]
        actObjFullArr.append(p)

    preprocessedAct = dictionary(actObjFullArr, BPMNdict)

    # 2. get the primitive command by GPT-3 classification
    # create JSON object with the preprocessed data
    JSONdata = {}
    JSONdata['activities'] = []
    for i in preprocessedAct:
        # get each classification result by GPT-3
        classification_results = nlp_classification_results(i[1], "file-I2XzSpsdqtEDxe4sMOcH87UH")
        # get corresponding command as primitive
        primitive = corr_label(classification_results)
        print(primitive)
        JSONdata['activities'].append(
            {
            'act_id': i[0],
            'act_name': i[1],
            'obj_id': i[2],
            'obj_name': i[3].replace(" ", "_"),
            'primitive': primitive
            })

    # create a file (input to GPT-3)
    with open(filename1.replace('.bpmn', '.json'), 'w') as outfile:
        json.dump(JSONdata, outfile, indent=4)

    # 3. output robot's programming code in ROS
    input_file = filename1.replace('.bpmn', '.json')

    my_file = open(input_file.replace('.json', '.py'), "w")
    f = open(input_file)
    data = json.load(f)

    for i in data['activities']:
        substitute(i['act_name'], i['act_id'], i['obj_name'], i['obj_id'], i['primitive'], my_file)
        #substitute(act_name, act_id, obj_name, obj_id, primitive):


    # my_file = open("ROSready.py")
    # content = my_file.read()
    # my_file.close()



if __name__ == "__main__":
    main()
