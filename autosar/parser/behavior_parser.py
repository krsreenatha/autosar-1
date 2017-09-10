from autosar.base import parseBooleanNode,parseBoolean,parseTextNode,parseIntNode,parseFloatNode,parseAdminDataNode
from autosar.behavior import *

class BehaviorParser(object):
   def __init__(self,pkg,version=3):
      self.version=version
      self.pkg=pkg

   def parseInternalBehavior(self,xmlRoot,dummy,parent):
      """AUTOSAR 3 Internal Behavior"""
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))
      componentRef = parseTextNode(xmlRoot.find('COMPONENT-REF'))
      multipleInstance = False
      xmlSupportMultipleInst = xmlRoot.find('SUPPORTS-MULTIPLE-INSTANTIATION')
      if (xmlSupportMultipleInst is not None) and (xmlSupportMultipleInst.text == 'true'):
         multipleInstance = True
      ws = parent.rootWS()
      assert(ws is not None)
      if (name is not None) and (componentRef is not None):
         internalBehavior = InternalBehavior(name, componentRef, multipleInstance, parent)
         swc = ws.find(componentRef)
         if swc is not None:
            swc.behavior=internalBehavior
         for xmlNode in xmlRoot.findall('./*'):
            if (xmlNode.tag == 'SHORT-NAME') or (xmlNode.tag == 'COMPONENT-REF') or (xmlNode.tag == 'SUPPORTS-MULTIPLE-INSTANTIATION'):
               continue
            if xmlNode.tag == 'EVENTS':
               for xmlEvent in xmlNode.findall('./*'):
                  event = None
                  if xmlEvent.tag == 'MODE-SWITCH-EVENT':
                     event = self.parseModeSwitchEvent(xmlEvent,internalBehavior)
                  elif xmlEvent.tag == 'TIMING-EVENT':
                     event = self.parseTimingEvent(xmlEvent,internalBehavior)
                  elif xmlEvent.tag == 'DATA-RECEIVED-EVENT':
                     event = self.parseDataReceivedEvent(xmlEvent,internalBehavior)
                  elif xmlEvent.tag == 'OPERATION-INVOKED-EVENT':
                     event = self.parseOperationInvokedEvent(xmlEvent,internalBehavior)
                  else:
                     raise NotImplementedError(xmlEvent.tag)
                  if event is not None:
                     internalBehavior.events.append(event)
                  else:
                     raise ValueError('event')
            elif xmlNode.tag == 'PORT-API-OPTIONS':
               for xmlOption in xmlNode.findall('./PORT-API-OPTION'):                  
                  portAPIOption = PortAPIOption(parseTextNode(xmlOption.find('PORT-REF')),parseBooleanNode(xmlOption.find('ENABLE-TAKE-ADDRESS')),parseBooleanNode(xmlOption.find('INDIRECT-API')))
                  if portAPIOption is not None: internalBehavior.portAPIOptions.append(portAPIOption)
            elif xmlNode.tag == 'RUNNABLES':
               for xmRunnable in xmlNode.findall('./RUNNABLE-ENTITY'):
                  runnableEntity = self.parseRunnableEntity(xmRunnable, internalBehavior)
                  if runnableEntity is not None:
                     internalBehavior.runnables.append(runnableEntity)
            elif xmlNode.tag == 'PER-INSTANCE-MEMORYS':               
               for xmlElem in xmlNode.findall('./PER-INSTANCE-MEMORY'):
                 perInstanceMemory = PerInstanceMemory(parseTextNode(xmlElem.find('SHORT-NAME')),parseTextNode(xmlElem.find('TYPE-DEFINITION')), internalBehavior)
                 if perInstanceMemory is not None: internalBehavior.perInstanceMemories.append(perInstanceMemory)
            elif xmlNode.tag == 'SERVICE-NEEDSS':
               for xmlElem in xmlNode.findall('./*'):
                  if xmlElem.tag=='SWC-NV-BLOCK-NEEDS':
                     swcNvBlockNeeds=self.parseSwcNvBlockNeeds(xmlElem)
                     if swcNvBlockNeeds is not None: internalBehavior.swcNvBlockNeeds.append(swcNvBlockNeeds)
                  else:
                     raise NotImplementedError(xmlElem.tag)
            elif xmlNode.tag == 'SHARED-CALPRMS':
               for xmlElem in xmlNode.findall('./*'):
                  if xmlElem.tag=='CALPRM-ELEMENT-PROTOTYPE':
                     calPrmElemPrototype=self.parseCalPrmElemPrototype(xmlElem, internalBehavior)
                     assert(calPrmElemPrototype is not None)
                     internalBehavior.sharedCalParams.append(calPrmElemPrototype)
                  else:
                     raise NotImplementedError(xmlElem.tag)
            elif xmlNode.tag == 'EXCLUSIVE-AREAS':
               for xmlElem in xmlNode.findall('./*'):
                  if xmlElem.tag=='EXCLUSIVE-AREA':
                     exclusiveArea=ExclusiveArea(parseTextNode(xmlElem.find('SHORT-NAME')), internalBehavior)
                     internalBehavior.exclusiveAreas.append(exclusiveArea)
                  else:
                     raise NotImplementedError(xmlElem.tag)
            else:
               raise NotImplementedError(xmlNode.tag)   
         return internalBehavior      

   def parseSWCInternalBehavior(self, xmlRoot, parent):
      """AUTOSAR 4 internal behavior"""
      assert(xmlRoot.tag == 'SWC-INTERNAL-BEHAVIOR')
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))               
      multipleInstance = False
      xmlSupportMultipleInst = xmlRoot.find('SUPPORTS-MULTIPLE-INSTANTIATION')
      if (xmlSupportMultipleInst is not None) and (xmlSupportMultipleInst.text == 'true'):
         multipleInstance = True      
      ws = parent.rootWS()
      assert(ws is not None)
      if (name is not None):
         handledXML = ['SHORT-NAME', 'SUPPORTS-MULTIPLE-INSTANTIATION'] 
         internalBehavior = InternalBehavior(name, parent.ref, multipleInstance, parent)      
         for xmlNode in xmlRoot.findall('./*'):
            if xmlNode.tag in handledXML:
               pass
            elif xmlNode.tag == 'DATA-TYPE-MAPPING-REFS':
               pass #not yet implemented
            elif xmlNode.tag == 'EVENTS':
                  for xmlEvent in xmlNode.findall('./*'):
                     event = None
                     if xmlEvent.tag == 'INIT-EVENT':
                        event = self.parseInitEvent(xmlEvent,internalBehavior)
                     elif xmlEvent.tag == 'SWC-MODE-SWITCH-EVENT':
                        event = self.parseModeSwitchEvent(xmlEvent,internalBehavior)
                     elif xmlEvent.tag == 'TIMING-EVENT':
                        event = self.parseTimingEvent(xmlEvent,internalBehavior)
                     elif xmlEvent.tag == 'DATA-RECEIVED-EVENT':
                        event = self.parseDataReceivedEvent(xmlEvent,internalBehavior)
                     elif xmlEvent.tag == 'OPERATION-INVOKED-EVENT':
                        event = self.parseOperationInvokedEvent(xmlEvent,internalBehavior)
                     else:
                        raise NotImplementedError(xmlEvent.tag)
                     if event is not None:
                        internalBehavior.events.append(event)
                     else:
                        raise NotImplementedError(xmlEvent.tag)
            elif xmlNode.tag == 'PORT-API-OPTIONS':
               for xmlOption in xmlNode.findall('./PORT-API-OPTION'):                  
                  portAPIOption = PortAPIOption(parseTextNode(xmlOption.find('PORT-REF')),parseBooleanNode(xmlOption.find('ENABLE-TAKE-ADDRESS')),parseBooleanNode(xmlOption.find('INDIRECT-API')))
                  if portAPIOption is not None: internalBehavior.portAPIOptions.append(portAPIOption)
            elif xmlNode.tag == 'RUNNABLES':
               for xmRunnable in xmlNode.findall('./RUNNABLE-ENTITY'):
                  runnableEntity = self.parseRunnableEntity(xmRunnable, parent)
                  if runnableEntity is not None:
                     internalBehavior.runnables.append(runnableEntity)                     
            else:
               raise NotImplementedError(xmlNode.tag)
         return internalBehavior

   def parseRunnableEntity(self, xmlRoot, parent):
      xmlDataReceivePoints=None
      xmlDataSendPoints=None
      xmlServerCallPoints=None
      xmlCanEnterExclusiveAreas=None
      adminData = None
      modeAccessPoints = None
      if self.version < 4.0:
         for xmlElem in xmlRoot.findall('*'):
            if xmlElem.tag=='SHORT-NAME':
               name=parseTextNode(xmlElem)
            elif xmlElem.tag=='CAN-BE-INVOKED-CONCURRENTLY':
               canBeInvokedConcurrently=parseBooleanNode(xmlElem)
            elif xmlElem.tag=='DATA-RECEIVE-POINTS':
               xmlDataReceivePoints=xmlElem
            elif xmlElem.tag=='DATA-SEND-POINTS':
               xmlDataSendPoints=xmlElem
            elif xmlElem.tag=='SERVER-CALL-POINTS':
               xmlServerCallPoints=xmlElem
            elif xmlElem.tag=='SYMBOL':
               symbol=parseTextNode(xmlElem)
            elif xmlElem.tag=='CAN-ENTER-EXCLUSIVE-AREA-REFS':
               xmlCanEnterExclusiveAreas=xmlElem
            elif xmlElem.tag=='ADMIN-DATA':
               adminData=parseAdminDataNode(xmlElem)
            else:
               raise NotImplementedError(xmlElem.tag)
      else:
         for xmlElem in xmlRoot.findall('*'):
            if xmlElem.tag=='SHORT-NAME':
               name=parseTextNode(xmlElem)
            elif xmlElem.tag=='CAN-BE-INVOKED-CONCURRENTLY':
               canBeInvokedConcurrently=parseBooleanNode(xmlElem)
            elif xmlElem.tag == 'MODE-ACCESS-POINTS':
               modeAccessPoints = xmlElem
            elif xmlElem.tag=='DATA-RECEIVE-POINT-BY-ARGUMENTS':
               xmlDataReceivePoints=xmlElem
            elif xmlElem.tag=='DATA-SEND-POINTS':
               xmlDataSendPoints=xmlElem
            elif xmlElem.tag=='SERVER-CALL-POINTS':
               xmlServerCallPoints=xmlElem
            elif xmlElem.tag=='SYMBOL':
               symbol=parseTextNode(xmlElem)
#            elif xmlElem.tag=='CAN-ENTER-EXCLUSIVE-AREA-REFS':
#               xmlCanEnterExclusiveAreas=xmlElem
            elif xmlElem.tag == 'MINIMUM-START-INTERVAL':
               pass #not implemented
            elif xmlElem.tag=='ADMIN-DATA':
               adminData=parseAdminDataNode(xmlElem)
            else:
               raise NotImplementedError(xmlElem.tag)
      runnableEntity = RunnableEntity(name, canBeInvokedConcurrently, symbol, parent)
      if xmlDataReceivePoints is not None:
         if self.version < 4.0:
            for xmlDataPoint in xmlDataReceivePoints.findall('./DATA-RECEIVE-POINT'):
               name=parseTextNode(xmlDataPoint.find('SHORT-NAME'))
               dataElementInstanceRef = self.parseDataElementInstanceRef(xmlDataPoint.find('DATA-ELEMENT-IREF'),'R-PORT-PROTOTYPE-REF')
               if dataElementInstanceRef is not None:
                  dataReceivePoint=DataReceivePoint(dataElementInstanceRef.portRef,dataElementInstanceRef.dataElemRef,name)
                  runnableEntity.append(dataReceivePoint)
         else:
            for xmlVariableAcess in xmlDataReceivePoints.findall('VARIABLE-ACCESS'):
               name=parseTextNode(xmlVariableAcess.find('SHORT-NAME'))               
               accessedVariable = self.parseAccessedVariable(xmlVariableAcess.find('./ACCESSED-VARIABLE'))
               assert(accessedVariable is not None)
               dataReceivePoint=DataReceivePoint(accessedVariable.portPrototypeRef,accessedVariable.targetDataPrototypeRef,name)
               runnableEntity.append(dataReceivePoint)
      if xmlDataSendPoints is not None:
         if self.version < 4.0:
            for xmlDataPoint in xmlDataSendPoints.findall('./DATA-SEND-POINT'):
               name=parseTextNode(xmlDataPoint.find('SHORT-NAME'))
               dataElementInstanceRef = self.parseDataElementInstanceRef(xmlDataPoint.find('DATA-ELEMENT-IREF'),'P-PORT-PROTOTYPE-REF')
               if dataElementInstanceRef is not None:
                  dataSendPoint=DataSendPoint(dataElementInstanceRef.portRef,dataElementInstanceRef.dataElemRef,name)
                  runnableEntity.append(dataSendPoint)
         else:
            for xmlVariableAcess in xmlDataSendPoints.findall('VARIABLE-ACCESS'):
               name=parseTextNode(xmlVariableAcess.find('SHORT-NAME'))               
               accessedVariable = self.parseAccessedVariable(xmlVariableAcess.find('./ACCESSED-VARIABLE'))
               assert(accessedVariable is not None)
               dataSendPoint=DataSendPoint(accessedVariable.portPrototypeRef,accessedVariable.targetDataPrototypeRef,name)
               runnableEntity.append(dataSendPoint)            
      if xmlServerCallPoints is not None:
         for xmlServerCallPoint in xmlServerCallPoints.findall('./SYNCHRONOUS-SERVER-CALL-POINT'):
            syncServerCallPoint = self.parseSyncServerCallPoint(xmlServerCallPoint)
            if syncServerCallPoint is not None: runnableEntity.serverCallPoints.append(syncServerCallPoint)
      if xmlCanEnterExclusiveAreas is not None:
         for xmlCanEnterExclusiveAreaRef in xmlCanEnterExclusiveAreas.findall('./CAN-ENTER-EXCLUSIVE-AREA-REF'):
            runnableEntity.exclusiveAreaRefs.append(parseTextNode(xmlCanEnterExclusiveAreaRef))                        
      if runnableEntity is not None:
         runnableEntity.adminData = adminData
      return runnableEntity


   def parseModeInstanceRef(self,xmlRoot,parent=None):
      """parses <MODE-IREF>"""      
      assert(xmlRoot.tag == 'MODE-IREF')
      if self.version < 4.0:
         modeDeclarationRef=parseTextNode(xmlRoot.find('MODE-DECLARATION-REF'))
         modeDeclarationGroupPrototypeRef = parseTextNode(xmlRoot.find('MODE-DECLARATION-GROUP-PROTOTYPE-REF'))
         requirePortPrototypeRef = parseTextNode(xmlRoot.find('R-PORT-PROTOTYPE-REF'))
      elif self.version >= 4.0:
         modeDeclarationRef=parseTextNode(xmlRoot.find('TARGET-MODE-DECLARATION-REF'))
         modeDeclarationGroupPrototypeRef = parseTextNode(xmlRoot.find('CONTEXT-MODE-DECLARATION-GROUP-PROTOTYPE-REF'))
         requirePortPrototypeRef = parseTextNode(xmlRoot.find('CONTEXT-PORT-REF'))
      else:
         raise NotImplemented('version: '+self.version)
      return ModeInstanceRef(modeDeclarationRef,modeDeclarationGroupPrototypeRef,requirePortPrototypeRef)

   def parseModeDependency(self,xmlRoot,parent=None):
      """parses <MODE-DEPENDENCY>"""
      assert(xmlRoot.tag == 'MODE-DEPENDENCY')
      modeDependency=ModeDependency()
      if xmlRoot.find('DEPENDENT-ON-MODE-IREFS') is not None:
         for xmlNode in xmlRoot.findall('./DEPENDENT-ON-MODE-IREFS/DEPENDENT-ON-MODE-IREF'):
            modeInstanceRef = self.parseDependentOnModeInstanceRef(xmlNode)
            if modeInstanceRef is not None:
               modeDependency.modeInstanceRefs.append(modeInstanceRef)
      return modeDependency
   

   def parseDependentOnModeInstanceRef(self,xmlRoot,parent=None):
      """parses <DEPENDENT-ON-MODE-IREF>"""
      assert(xmlRoot.tag == 'DEPENDENT-ON-MODE-IREF')      
      modeDeclarationRef=parseTextNode(xmlRoot.find('MODE-DECLARATION-REF'))
      modeDeclarationGroupPrototypeRef = parseTextNode(xmlRoot.find('MODE-DECLARATION-GROUP-PROTOTYPE-REF'))
      requirePortPrototypeRef = parseTextNode(xmlRoot.find('R-PORT-PROTOTYPE-REF'))
      return ModeDependencyRef(modeDeclarationRef,modeDeclarationGroupPrototypeRef,requirePortPrototypeRef)    

   def parseInitEvent(self,xmlNode,parent=None):
      name = parseTextNode(xmlNode.find('SHORT-NAME'))      
      startOnEventRef = parseTextNode(xmlNode.find('START-ON-EVENT-REF'))
      initEvent=InitEvent(name, startOnEventRef, parent)
      return initEvent
      
      
   def parseModeSwitchEvent(self,xmlNode,parent=None):
      """parses AUTOSAR3 <MODE-SWITCH-EVENT>"""
      if self.version < 4.0:
         assert(xmlNode.tag=='MODE-SWITCH-EVENT')
         name = parseTextNode(xmlNode.find('SHORT-NAME'))      
         modeInstRef = self.parseModeInstanceRef(xmlNode.find('MODE-IREF'))
         startOnEventRef = parseTextNode(xmlNode.find('START-ON-EVENT-REF'))
         activation = parseTextNode(xmlNode.find('ACTIVATION'))
         modeSwitchEvent=ModeSwitchEvent(name, startOnEventRef, activation, parent, self.version)
         modeSwitchEvent.modeInstRef=modeInstRef
      elif self.version >= 4.0:
         assert(xmlNode.tag=='SWC-MODE-SWITCH-EVENT')
         name = parseTextNode(xmlNode.find('SHORT-NAME'))
         modeInstanceRefs = []
         for xmlElem in xmlNode.findall('./MODE-IREFS/*'):
            if xmlElem.tag == 'MODE-IREF':
               modeInstanceRefs.append(self.parseModeInstanceRef(xmlElem))
            else:
               raise NotImplementedError(xmlElem.tag)            
         startOnEventRef = parseTextNode(xmlNode.find('START-ON-EVENT-REF'))
         activation = parseTextNode(xmlNode.find('ACTIVATION'))
         modeSwitchEvent=ModeSwitchEvent(name, startOnEventRef, activation, parent, self.version)
         modeSwitchEvent.modeInstRef=modeInstanceRefs
      else:
         raise NotImplementedError('version: '+self.version)
      return modeSwitchEvent

   def parseTimingEvent(self,xmlNode,parent=None):
      name = parseTextNode(xmlNode.find('SHORT-NAME'))      
      startOnEventRef = parseTextNode(xmlNode.find('START-ON-EVENT-REF'))
      period=parseTextNode(xmlNode.find('PERIOD'))
      if period is None:
         period=0.0
      timingEvent=TimingEvent(name, startOnEventRef, float(period)*1000, parent)
      xmlModeDependency = xmlNode.find('MODE-DEPENDENCY')
      if xmlModeDependency is not None:
         timingEvent.modeDependency = self.parseModeDependency(xmlModeDependency, parent)
      return timingEvent

   
   def parseDataReceivedEvent(self,xmlRoot,parent=None):
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))      
      startOnEventRef = parseTextNode(xmlRoot.find('START-ON-EVENT-REF'))
      dataInstanceRef=self.parseDataInstanceRef(xmlRoot.find('DATA-IREF'),'R-PORT-PROTOTYPE-REF')
      dataReceivedEvent=DataReceivedEvent(name, startOnEventRef, parent)
      xmlModeDependency = xmlRoot.find('MODE-DEPENDENCY')
      if xmlModeDependency is not None:
         dataReceivedEvent.modeDependency = self.parseModeDependency(xmlModeDependency)
      dataReceivedEvent.dataInstanceRef=dataInstanceRef
      return dataReceivedEvent

   def parseOperationInvokedEvent(self,xmlRoot,parent=None):
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))      
      startOnEventRef = parseTextNode(xmlRoot.find('START-ON-EVENT-REF'))
      operationInstanceRef=self.parseOperationInstanceRef(xmlRoot.find('OPERATION-IREF'),'P-PORT-PROTOTYPE-REF')
      operationInvokedEvent=OperationInvokedEvent(name, startOnEventRef, parent)
      xmlModeDependency = xmlRoot.find('MODE-DEPENDENCY')
      if xmlModeDependency is not None:
         operationInvokedEvent.modeDependency = self.parseModeDependency(xmlModeDependency)
      operationInvokedEvent.operationInstanceRef=operationInstanceRef
      return operationInvokedEvent

   
   def parseDataInstanceRef(self,xmlRoot,portTag):
      """parses <DATA-IREF>"""
      assert(xmlRoot.tag=='DATA-IREF')
      assert(xmlRoot.find(portTag) is not None)      
      return DataInstanceRef(parseTextNode(xmlRoot.find(portTag)),parseTextNode(xmlRoot.find('DATA-ELEMENT-PROTOTYPE-REF')))

   def parseOperationInstanceRef(self,xmlRoot,portTag):
      """parses <OPERATION-IREF>"""      
      assert(xmlRoot.tag=='OPERATION-IREF')
      assert(xmlRoot.find(portTag) is not None)
      
      if self.version >= 4.0:
         if portTag == 'CONTEXT-P-PORT-REF':
            operationTag = 'TARGET-PROVIDED-OPERATION-REF'            
         else:
            operationTag = 'TARGET-REQUIRED-OPERATION-REF'
      else:         
         operationTag = 'OPERATION-PROTOTYPE-REF'
      return OperationInstanceRef(parseTextNode(xmlRoot.find(portTag)),parseTextNode(xmlRoot.find(operationTag)))
      

   def parseDataElementInstanceRef(self,xmlRoot,portTag):
      """parses <DATA-ELEMENT-IREF>"""
      assert(xmlRoot.tag=='DATA-ELEMENT-IREF')
      assert(xmlRoot.find(portTag) is not None)      
      return DataElementInstanceRef(parseTextNode(xmlRoot.find(portTag)),parseTextNode(xmlRoot.find('DATA-ELEMENT-PROTOTYPE-REF')))

   def parseSwcNvBlockNeeds(self,xmlRoot):
      name=parseTextNode(xmlRoot.find('SHORT-NAME'))
      numberOfDataSets=parseIntNode(xmlRoot.find('N-DATA-SETS'))
      readOnly=parseBooleanNode(xmlRoot.find('READONLY'))
      reliability=parseTextNode(xmlRoot.find('RELIABILITY'))
      resistantToChangedSW=parseBooleanNode(xmlRoot.find('RESISTANT-TO-CHANGED-SW'))
      restoreAtStart=parseBooleanNode(xmlRoot.find('RESTORE-AT-START'))
      writeOnlyOnce=parseBooleanNode(xmlRoot.find('WRITE-ONLY-ONCE'))
      writingFrequency=parseIntNode(xmlRoot.find('WRITING-FREQUENCY'))
      writingPriority=parseTextNode(xmlRoot.find('WRITING-PRIORITY'))
      defaultBlockRef=parseTextNode(xmlRoot.find('DEFAULT-BLOCK-REF'))
      mirrorBlockRef=parseTextNode(xmlRoot.find('MIRROR-BLOCK-REF'))      
      serviceCallPorts=self.parseServiceCallPorts(xmlRoot.find('SERVICE-CALL-PORTS'))
      assert(len(serviceCallPorts)>0)
      swcNvBlockNeeds=SwcNvBlockNeeds(name,numberOfDataSets,readOnly,reliability,resistantToChangedSW,restoreAtStart,
                                      writeOnlyOnce,writingFrequency,writingPriority,defaultBlockRef,mirrorBlockRef)
      swcNvBlockNeeds.serviceCallPorts=serviceCallPorts
      return swcNvBlockNeeds

   def parseServiceCallPorts(self,xmlRoot):
      """parses <SERVICE-CALL-PORTS>"""
      assert(xmlRoot.tag=='SERVICE-CALL-PORTS')
      serviceCallPorts=[]
      for xmlNode in xmlRoot.findall('ROLE-BASED-R-PORT-ASSIGNMENT'):
         roleBasedRPortAssignment=RoleBasedRPortAssignment(parseTextNode(xmlNode.find('R-PORT-PROTOTYPE-REF')),parseTextNode(xmlNode.find('ROLE')))         
         serviceCallPorts.append(roleBasedRPortAssignment)
      return serviceCallPorts
   
   def parseCalPrmElemPrototype(self, xmlRoot, parent):
      """
      parses <CALPRM-ELEMENT-PROTOTYPE>
      """
      name = parseTextNode(xmlRoot.find('SHORT-NAME'))
      adminData=parseAdminDataNode(xmlRoot.find('ADMIN-DATA'))
      typeRef = parseTextNode(xmlRoot.find('TYPE-TREF'))
      calPrmElemPrototype = CalPrmElemPrototype(name, typeRef, parent, adminData)
      for xmlElem in xmlRoot.findall('./SW-DATA-DEF-PROPS/*'):
         if xmlElem.tag=='SW-ADDR-METHOD-REF':
            calPrmElemPrototype.swDataDefsProps.append(parseTextNode(xmlElem))
         else:
            raise NotImplementedError(xmlElem.tag)
      return calPrmElemPrototype
   
   def parseSyncServerCallPoint(self, xmlRoot):
      """
      parses <SYNCHRONOUS-SERVER-CALL-POINT>
      """
      assert(xmlRoot.tag=='SYNCHRONOUS-SERVER-CALL-POINT')
      if self.version >= 4.0:
         operationInstanceRefs=[]
         for xmlElem in xmlRoot.findall('*'):
            if xmlElem.tag=='SHORT-NAME':
               name=parseTextNode(xmlElem)            
            elif xmlElem.tag=='OPERATION-IREF':
               operationInstanceRefs.append(self.parseOperationInstanceRef(xmlElem,'CONTEXT-R-PORT-REF'))
            elif xmlElem.tag=='TIMEOUT':
               timeout=parseFloatNode(xmlElem)
            else:
               raise NotImplementedError(xmlElem.tag)
      else:
         for xmlElem in xmlRoot.findall('*'):
            if xmlElem.tag=='SHORT-NAME':
               name=parseTextNode(xmlElem)            
            elif xmlElem.tag=='OPERATION-IREFS':
               operationInstanceRefs=[]
               for xmlOperation in xmlElem.findall('*'):
                  if xmlOperation.tag=='OPERATION-IREF':
                     operationInstanceRefs.append(self.parseOperationInstanceRef(xmlOperation,'R-PORT-PROTOTYPE-REF'))
                  else:
                     raise NotImplementedError(xmlElem.tag)
            elif xmlElem.tag=='TIMEOUT':
               timeout=parseFloatNode(xmlElem)
            else:
               raise NotImplementedError(xmlElem.tag)         
      retval=SyncServerCallPoint(name,timeout)
      retval.operationInstanceRefs=operationInstanceRefs
      return retval

   def parseAccessedVariable(self, xmlRoot):
      assert(xmlRoot.tag == 'ACCESSED-VARIABLE')
      xmlPortPrototypeRef = xmlRoot.find('./AUTOSAR-VARIABLE-IREF/PORT-PROTOTYPE-REF')
      xmlTargetDataPrototypeRef = xmlRoot.find('./AUTOSAR-VARIABLE-IREF/TARGET-DATA-PROTOTYPE-REF')
      assert (xmlPortPrototypeRef is not None)
      assert (xmlTargetDataPrototypeRef is not None)
      return VariableAccess(parseTextNode(xmlRoot.find('SHORT-NAME')),parseTextNode(xmlPortPrototypeRef), parseTextNode(xmlTargetDataPrototypeRef))
