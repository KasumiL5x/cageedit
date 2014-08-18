import sys
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya

# -*- Plugin information -*-
plugin_node_name = 'pushDeformer'
plugin_node_id = OpenMaya.MTypeId(0x1C3B0475)

class PushDeformerNode(OpenMayaMPx.MPxDeformerNode):
	# Amount to push the vertices by
	inflation_attr = OpenMaya.MObject()

	def __init__(self):
		OpenMayaMPx.MPxDeformerNode.__init__(self)
	#END

	def deform(self, data, geom_it, local_to_world_mat, geom_idx):
		envelope_attr = OpenMayaMPx.cvar.MPxDeformerNode_envelope
		envelope = data.inputValue(envelope_attr).asFloat()

		inflation_handle = data.inputValue(PushDeformerNode.inflation_attr)
		inflation = inflation_handle.asDouble()

		input_geom_obj = self.get_input_geom(data, geom_idx)
		normals = OpenMaya.MFloatVectorArray()
		mesh = OpenMaya.MFnMesh(input_geom_obj)
		mesh.getVertexNormals(True, normals, OpenMaya.MSpace.kTransform)

		while not geom_it.isDone():
			idx = geom_it.index()
			nrm = OpenMaya.MVector(normals[idx])
			pos = geom_it.position()
			new_pos = pos + (nrm * inflation * envelope)
			geom_it.setPosition(new_pos)
			geom_it.next()
	#END

	def get_input_geom(self, data, geom_idx):
		input_attr = OpenMayaMPx.cvar.MPxDeformerNode_input
		input_geom_attr = OpenMayaMPx.cvar.MPxDeformerNode_inputGeom
		input_handle = data.outputArrayValue(input_attr)
		input_handle.jumpToElement(geom_idx)
		input_geom_obj = input_handle.outputValue().child(input_geom_attr).asMesh()
		return input_geom_obj
	#END
#END

def node_creator():
	return OpenMayaMPx.asMPxPtr(PushDeformerNode())
#END

def node_initializer():
	num_attr = OpenMaya.MFnNumericAttribute()

	# Setup attributes
	PushDeformerNode.inflation_attr = num_attr.create('inflation', 'in', OpenMaya.MFnNumericData.kDouble, 0.0)
	num_attr.setMin(0.0)
	num_attr.setMax(10.0)
	num_attr.setChannelBox(True)
	PushDeformerNode.addAttribute(PushDeformerNode.inflation_attr)

	# Link inputs that change the output of the mesh
	PushDeformerNode.attributeAffects(PushDeformerNode.inflation_attr, OpenMayaMPx.cvar.MPxDeformerNode_outputGeom)
#END

def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.registerNode(plugin_node_name, plugin_node_id, node_creator, node_initializer, OpenMayaMPx.MPxNode.kDeformerNode)
	except:
		sys.stderr.write('Failed to register node: ' + plugin_node_name)
		raise
#END

def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterNode(plugin_node_id)
	except:
		sys.stderr.write('Failed to deregister node: ' + plugin_node_name)
		raise
#END
