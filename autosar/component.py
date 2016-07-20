from autosar.base import parseXMLFile,splitref,parseTextNode,parseIntNode
from autosar.element import Element
import autosar.portinterface
import autosar.constant
#from autosar.behavior import ModeSwitchEvent,TimingEvent,ModeDependency,ModeInstanceRef,PortAPIOption,RunnableEntity,DataElementInstanceRef,InternalBehavior,BehaviorParser
import json
import sys

def _getDataElemNameFromComSpec(xmlElem,portInterfaceRef):
   if xmlElem.find('./DATA-ELEMENT-REF') is not None:
      dataElemRef = splitref(xmlElem.find('./DATA-ELEMENT-REF').text)
      assert(dataElemRef is not None)
      dataElemName = dataElemRef.pop()
      tmp = '/'+'/'.join(dataElemRef)
      if portInterfaceRef == tmp:
         return dataElemName
   return None

def _getOperationNameFromComSpec(xmlElem,portInterfaceRef):
   xmlOperation=xmlElem.find('./OPERATION-REF')
   if xmlOperation is not None:
      operationRef = splitref(xmlOperation.text)
      assert(operationRef is not None)
      operationName = operationRef.pop()
      tmp = '/'+'/'.join(operationRef)
      if portInterfaceRef == tmp:
         return operationName
   return None

class ComponentType(Element):
   def __init__(self,name,parent=None):
      super().__init__(name,parent)      
      self.requirePorts=[]
      self.providePorts=[]
      self.behavior=None
      self.implementation=None
   
   def asdict(self):
      data={'type': self.__class__.__name__,'name':self.name,'requirePorts':[],'providePorts':[]}
      for port in self.requirePorts:
         data['requirePorts'].append(port.asdict())
      for port in self.providePorts:
         data['providePorts'].append(port.asdict())
      if len(data['requirePorts'])==0: del data['requirePorts']
      if len(data['providePorts'])==0: del data['providePorts']
      return data
   
   def findByRef(self,ref):
      ref=ref.partition('/')      
      for port in self.requirePorts:
         if port.name == ref[0]:
            return port
      for port in self.providePorts:
         if port.name == ref[0]:
            return port
      return None
   
   def append(self, elem):
      if isinstance(elem,RequirePort):
         self.requirePorts.append(elem)
         elem.parent=self
      elif isinstance(elem,ProvidePort):
         self.providePorts.append(elem)
         elem.parent=self
      else:
         raise ValueError("unexpected type:" + str(type(elem)))
   

class ApplicationSoftwareComponent(ComponentType):
   def __init__(self,name,parent=None):
      super().__init__(name,parent)

class ComplexDeviceDriverSoftwareComponent(ComponentType):
   def __init__(self,name,parent=None):
      super().__init__(name,parent)

class Port(object):
   def __init__(self,name,portInterfaceRef,parent=None):
      self.name = name      
      if portInterfaceRef is not None and not isinstance(portInterfaceRef,str):
         raise ValueError('portInterfaceRef needs to be of type None or str')
      self.portInterfaceRef = portInterfaceRef
      self.comspec=[] 
      self.parent=parent
   @property
   def ref(self):
      if self.parent is not None:
         return self.parent.ref+'/%s'%self.name
      else:
         return '/%s'%self.name

   
   def asdict(self):
      data={'type': self.__class__.__name__,'name':self.name, 'portInterfaceRef':self.portInterfaceRef, 'attributes':[]}
      for attribute in self.attributes:
         data['attributes'].append(attribute.asdict())
      if len(data['attributes'])==0: del data['attributes']
      return data
   
   def createComSpecFromDict(self,ws,portInterfaceRef,comspec):
      assert(ws is not None)
      assert(isinstance(comspec,dict))
      portInterface=ws.find(portInterfaceRef)
      if portInterface is None:
         raise ValueError("port interface not found: "+portInterfaceRef)
      if isinstance(portInterface,autosar.portinterface.SenderReceiverInterface):
         name=None
         initValueRef=None
         aliveTimeout=None
         queueLength=None
         if 'name' in comspec: name=str(comspec['name'])
         if 'initValueRef' in comspec: initValueRef=str(comspec['initValueRef'])
         if 'aliveTimeout' in comspec: aliveTimeout=int(comspec['aliveTimeout'])
         if 'queueLength' in comspec: queueLength=int(comspec['queueLength'])
         if name is None:
            name=portInterface.dataElements[0].name #pick the name of the first available data element in portInterface
         #verify (user-supplied) name
         dataElement=portInterface.find(name)
         if dataElement is None:
            raise ValueError("unknown element '%s' of portInterface '%s'"%(name,portInterface.name))
         #verify compatibility of initValueRef
         if initValueRef is not None:
            initValue = ws.find(initValueRef)
            if initValue is None:
               raise ValueError("invalid reference detected: '%s'"%initValueRef)
            if isinstance(initValue,autosar.Constant):
               if dataElement.typeRef != initValue.value.typeRef:
                  raise ValueError("constant value has different type from data element, expected '%s', found '%s'"%(dataElement.typeRef,initValue.value.typeRef))
            else:
               raise ValueError("reference is not a Constant object: '%s'"%initValueRef)
         self.comspec.append(DataElementComSpec(name,initValueRef,aliveTimeout,queueLength))
            
      
class RequirePort(Port):
   def __init__(self,name,portInterfaceRef=None,comspec=None,parent=None):
      super().__init__(name,portInterfaceRef,parent)
      if comspec is not None:
         ws = autosar.getCurrentWS()
         assert(ws is not None)
         if isinstance(comspec,dict):
            self.createComSpecFromDict(ws,portInterfaceRef,comspec)               
         else:
            raise NotImplementedError("not yet supported")

class ProvidePort(Port):
   def __init__(self,name,portInterfaceRef=None,comspec=None,parent=None):
      super().__init__(name,portInterfaceRef,parent)
      if comspec is not None:
         ws = autosar.getCurrentWS()
         assert(ws is not None)
         if isinstance(comspec,dict):
            self.createComSpecFromDict(ws,comspec)               
         else:
            raise NotImplementedError("not yet supported")

class OperationComSpec(object):
   def __init__(self,name=None,queueLength=None):
      self.name = name
      self.queueLength=None
   def asdict(self):
      data={'type': self.__class__.__name__,'name':self.name}
      if self.queueLength is not None:
         data['queueLength']=self.queueLength

class DataElementComSpec(object):
   def __init__(self,name=None,initValueRef=None,aliveTimeout=None,queueLength=None):
      self.name = name
      self.initValueRef = initValueRef
      self._aliveTimeout = aliveTimeout
      self._queueLength = queueLength
   @property
   def aliveTimeout(self):
      return self._aliveTimeout
   
   @aliveTimeout.setter
   def aliveTimeout(self,val):      
      self._aliveTimeout = int(val)

   @property
   def queueLength(self):
      return self._queueLength
   
   @queueLength.setter
   def queueLength(self,val):      
      self._queueLength = int(val)
   
   def asdict(self):
      data={'type': self.__class__.__name__,'name':self.name}
      if self.initValueRef is not None: data['initValueRef']=self.initValueRef
      if self.aliveTimeout is not None: data['aliveTimeout']=self.aliveTimeout
      if self.queueLength is not None: data['queueLength']=self.queueLength
      return data

class SwcImplementation(Element):
   def __init__(self,name,behaviorRef,parent=None):
      super().__init__(name,parent)
      self.behaviorRef=behaviorRef

class CompositionType(Element):
   def __init__(self,name,parent=None):
      super().__init__(name,parent) 
      self.requirePorts=[]
      self.providePorts=[]
      self.components=[]
      self.assemblyConnectors=[]
      self.delegationConnectors=[]
   
   def asdict(self):
      data={'type': self.__class__.__name__,'name':self.name,'requirePorts':[],'providePorts':[],'components':[],
         'assemblyConnectors':[], 'delegationConnectors':[]}
      for port in self.requirePorts:
         data['requirePorts'].append(port.asdict())
      for port in self.providePorts:
         data['providePorts'].append(port.asdict())
      for component in self.components:
         data['components'].append(component.asdict())
      for connector in self.assemblyConnectors:
         data['assemblyConnectors'].append(connector.asdict())
      for connector in self.delegationConnectors:
         data['delegationConnectors'].append(connector.asdict())
      if len(data['requirePorts'])==0: del data['requirePorts']
      if len(data['providePorts'])==0: del data['providePorts']
      if len(data['components'])==0: del data['components']
      if len(data['assemblyConnectors'])==0: del data['assemblyConnectors']
      if len(data['delegationConnectors'])==0: del data['delegationConnectors']
      return data

class ComponentPrototype:
   def __init__(self,name,typeRef,parent=None):
      self.name=name
      self.typeRef=typeRef
      self.parent=parent
   def asdict(self):
      return {'type': self.__class__.__name__,'name':self.name,'typeRef':self.typeRef}
   @property
   def ref(self):
      if self.parent is not None:
         return self.parent.ref+'/%s'%self.name
      else:
         return '/%s'%self.name




class ProviderInstanceRef:
   """
   <PROVIDER-IREF>
   """
   def __init__(self,componentRef,providePortRef):
      self.componentRef=componentRef
      self.providePortRef=providePortRef
   def asdict(self):
      return {'type': self.__class__.__name__,'componentRef':self.componentRef,'providePortRef':self.providePortRef}


class RequesterInstanceRef:
   """
   <REQUESTER-IREF>
   """
   def __init__(self,componentRef,requirePortRef):
      self.componentRef=componentRef
      self.requirePortRef=requirePortRef
   def asdict(self):
      return {'type': self.__class__.__name__,'componentRef':self.componentRef,'requirePortRef':self.requirePortRef}

class InnerPortInstanceRef:
   """
   <INNER-PORT-IREF>
   """
   def __init__(self,componentRef,portRef):
      self.componentRef=componentRef
      self.portRef=portRef
   def asdict(self):
      return {'type': self.__class__.__name__,'componentRef':self.componentRef,'portRef':self.portRef}
   
class AssemblyConnector(object):
   """
   <ASSEMBLY-CONNECTOR-PROTOTYPE>
   """
   def __init__(self,name,providerInstanceRef,requesterInstanceRef):
      assert(isinstance(providerInstanceRef,ProviderInstanceRef))
      assert(isinstance(requesterInstanceRef,RequesterInstanceRef))
      self.name=name
      self.providerInstanceRef=providerInstanceRef
      self.requesterInstanceRef=requesterInstanceRef
   def asdict(self):
      return {'type': self.__class__.__name__,'providerInstanceRef':self.providerInstanceRef.asdict(),'requesterInstanceRef':self.requesterInstanceRef.asdict()}

class DelegationConnector:
   """
   <DELEGATION-CONNECTOR-PROTOTYPE>
   """
   def __init__(self,name,innerPortInstanceRef):
      assert(isinstance(innerPortInstanceRef,InnerPortInstanceRef))
      self.name=name
      self.innerPortInstanceRef=innerPortInstanceRef
   def asdict(self):
      return {'type': self.__class__.__name__,'innerPortInstanceRef':self.innerPortInstanceRef.asdict()}

class ComponentTypeParser(object):
   """
   ComponentType parser   
   """
   def __init__(self,pkg,version=3):
      if version == 3:
         self.version=version
      else:
         raise NotImplementedError('Version %d of ARXML not supported'%version)
      self.pkg=pkg
   
   
   def loadFromXML(self,root):
      """loads constants from a constants package"""
      if self.version == 3:
         for xmlElem in root.findall('./ELEMENTS/*'):
            componentType = None
            if xmlElem.tag == 'APPLICATION-SOFTWARE-COMPONENT-TYPE':
               componentType = self.parseApplicationSoftwareComponent(xmlElem)
               if componentType is not None:
                  self.pkg.elements.append(componentType)
                              
   def parseSoftwareComponent(self,xmlRoot,rootProject=None,parent=None):
      componentType=None
      if xmlRoot.tag=='APPLICATION-SOFTWARE-COMPONENT-TYPE':
         componentType = ApplicationSoftwareComponent(parseTextNode(xmlRoot.find('SHORT-NAME')),parent)
      elif xmlRoot.tag=='COMPLEX-DEVICE-DRIVER-COMPONENT-TYPE':
         componentType=ComplexDeviceDriverSoftwareComponent(parseTextNode(xmlRoot.find('SHORT-NAME')),parent)
      else:
         raise NotImplementedError(xmlRoot.tag)
      self.parseComponentPorts(componentType,xmlRoot)
      return componentType
   
   def parseComponentPorts(self,componentType,xmlRoot):
      xmlPorts=xmlRoot.find('PORTS')
      assert(xmlPorts is not None)      
      for xmlPort in xmlPorts.findall('*'):
         if(xmlPort.tag == "R-PORT-PROTOTYPE"):
            portName = xmlPort.find('SHORT-NAME').text
            portInterfaceRef = xmlPort.find('REQUIRED-INTERFACE-TREF').text
            port = RequirePort(portName,portInterfaceRef,parent=componentType)                        
            if xmlPort.findall('./REQUIRED-COM-SPECS') is not None:        
               for xmlItem in xmlPort.findall('./REQUIRED-COM-SPECS/*'):
                  if xmlItem.tag == 'CLIENT-COM-SPEC':
                     operationName=_getOperationNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib=OperationComSpec(operationName)
                     port.attributes.append(attrib)
                  elif xmlItem.tag == 'UNQUEUED-RECEIVER-COM-SPEC':
                     dataElemName = _getDataElemNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib = DataElementComSpec(dataElemName)
                     if xmlItem.find('./ALIVE-TIMEOUT') != None:
                        attrib.aliveTimeout = xmlItem.find('./ALIVE-TIMEOUT').text
                     if xmlItem.find('./INIT-VALUE-REF') != None:
                        attrib.initValueRef = xmlItem.find('./INIT-VALUE-REF').text
                     port.attributes.append(attrib)
                  elif xmlItem.tag == 'QUEUED-RECEIVER-COM-SPEC':
                     dataElemName = _getDataElemNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib = DataElementComSpec(dataElemName)
                     if xmlItem.find('./QUEUE-LENGTH') != None:
                        attrib.queueLength = parseTextNode(xmlItem.find('./QUEUE-LENGTH'))
                     port.attributes.append(attrib)
                  else:
                     raise NotImplementedError(item.tag)
            componentType.requirePorts.append(port)
         elif(xmlPort.tag == 'P-PORT-PROTOTYPE'):
            portName = xmlPort.find('SHORT-NAME').text
            portInterfaceRef = xmlPort.find('PROVIDED-INTERFACE-TREF').text
            port = ProvidePort(portName,portInterfaceRef,parent=componentType)                                       
            if xmlPort.findall('./PROVIDED-COM-SPECS') is not None:
               for xmlItem in xmlPort.findall('./PROVIDED-COM-SPECS/*'):
                  if xmlItem.tag == 'SERVER-COM-SPEC':
                     operationName=_getOperationNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib=OperationComSpec(operationName)
                     attrib.queueLength=parseIntNode(xmlItem.find('QUEUE-LENGTH'))
                     port.attributes.append(attrib)
                  elif xmlItem.tag == 'UNQUEUED-SENDER-COM-SPEC':
                     dataElemName = _getDataElemNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib = DataElementComSpec(dataElemName)
                     if xmlItem.find('./INIT-VALUE-REF') != None:
                        attrib.initValueRef = xmlItem.find('./INIT-VALUE-REF').text
                     port.attributes.append(attrib)
                  elif xmlItem.tag == 'QUEUED-SENDER-COM-SPEC':
                     dataElemName = _getDataElemNameFromComSpec(xmlItem,portInterfaceRef)
                     attrib = DataElementComSpec(dataElemName)
                     port.attributes.append(attrib)
                  else:
                     raise NotImplementedError(xmlItem.tag)
            componentType.providePorts.append(port)      

   def parseSwcImplementation(self,xmlRoot,dummy,parent=None):
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))
      behaviorRef = parseTextNode(xmlRoot.find('BEHAVIOR-REF'))      
      impl = SwcImplementation(name,behaviorRef,parent=parent)
      return impl
   
   def parseCompositionType(self,xmlRoot,dummy,parent=None):
      """
      parses COMPOSITION-TYPE
      """
      assert(xmlRoot.tag=='COMPOSITION-TYPE')
      swc=CompositionType(parseTextNode(xmlRoot.find('SHORT-NAME')),parent)
      for elem in xmlRoot.findall('./*'):
         if elem.tag=='SHORT-NAME':
            continue
         if elem.tag=='PORTS':
            self.parseComponentPorts(swc,xmlRoot)
         elif elem.tag=='COMPONENTS':
            self.parseComponents(elem,swc)
         elif elem.tag=='CONNECTORS':
            self.parseConnectors(elem,swc)
         else:
            raise NotImplementedError(elem.tag)
      return swc
      
   def parseComponents(self,xmlRoot,parent):
      """
      parses <COMPONENTS>
      """
      assert(xmlRoot.tag=='COMPONENTS')
      for elem in xmlRoot.findall('./*'):
         if elem.tag=='COMPONENT-PROTOTYPE':
            name=parseTextNode(elem.find('SHORT-NAME'))
            typeRef=parseTextNode(elem.find('TYPE-TREF'))
            parent.components.append(ComponentPrototype(name,typeRef,parent))
         else:
            raise NotImplementedError(elem.tag)

   def parseConnectors(self,xmlRoot,parent=None):
      """
      parses <CONNECTORS>
      """
      assert(xmlRoot.tag=='CONNECTORS')
      for elem in xmlRoot.findall('./*'):
         if elem.tag=='ASSEMBLY-CONNECTOR-PROTOTYPE':
            name=parseTextNode(elem.find('SHORT-NAME'))
            providerComponentRef=parseTextNode(elem.find('./PROVIDER-IREF/COMPONENT-PROTOTYPE-REF'))
            providerPortRef=parseTextNode(elem.find('./PROVIDER-IREF/P-PORT-PROTOTYPE-REF'))
            requesterComponentRef=parseTextNode(elem.find('./REQUESTER-IREF/COMPONENT-PROTOTYPE-REF'))
            requesterPortRef=parseTextNode(elem.find('./REQUESTER-IREF/R-PORT-PROTOTYPE-REF'))
            parent.assemblyConnectors.append(AssemblyConnector(name,
                                                               ProviderInstanceRef(providerComponentRef,providerPortRef),
                                                               RequesterInstanceRef(requesterComponentRef,requesterPortRef)))
         elif elem.tag=='DELEGATION-CONNECTOR-PROTOTYPE':
            name=parseTextNode(elem.find('SHORT-NAME'))
            innerComponentRef=parseTextNode(elem.find('./INNER-PORT-IREF/COMPONENT-PROTOTYPE-REF'))
            innerPortRef=parseTextNode(elem.find('./INNER-PORT-IREF/PORT-PROTOTYPE-REF'))
            parent.delegationConnectors.append(DelegationConnector(name,InnerPortInstanceRef(innerComponentRef,innerPortRef)))
         else:
            raise NotImplementedError(elem.tag)
   

   
