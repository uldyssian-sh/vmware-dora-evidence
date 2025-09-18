"""
VMware vCenter API client for data collection.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import ssl

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from ..utils.logger import setup_logger


class VMwareClient:
    """Client for interacting with VMware vCenter APIs."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize VMware client.
        
        Args:
            config: VMware configuration dictionary
        """
        self.config = config
        self.logger = setup_logger(__name__)
        self.service_instance = None
        self.content = None
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Establish connection to vCenter."""
        try:
            # Get connection parameters from config
            host = self.config.get('vcenter_host')
            username = self.config.get('username')
            password = self.config.get('password')
            port = self.config.get('port', 443)
            
            if not all([host, username, password]):
                raise ValueError("Missing required VMware connection parameters")
            
            # Create SSL context with secure defaults
            context = ssl.create_default_context()
            
            # Only disable SSL verification if explicitly configured (not recommended for production)
            ignore_ssl = self.config.get('ignore_ssl_errors', False)
            if ignore_ssl:
                self.logger.warning("SSL certificate verification is disabled - use only in development/testing")
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            else:
                # Use secure defaults for production
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
            
            # Connect to vCenter
            self.service_instance = SmartConnect(
                host=host,
                user=username,
                pwd=password,
                port=port,
                sslContext=context
            )
            
            self.content = self.service_instance.RetrieveContent()
            self.logger.info(f"Successfully connected to vCenter: {host}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to vCenter: {str(e)}")
            raise
    
    def disconnect(self):
        """Disconnect from vCenter."""
        if self.service_instance:
            try:
                Disconnect(self.service_instance)
                self.logger.info("Disconnected from vCenter")
            except Exception as e:
                self.logger.warning(f"Error during disconnect: {str(e)}")
    
    def get_events(
        self, 
        event_types: List[str], 
        start_time: datetime, 
        end_time: datetime,
        max_events: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events from vCenter.
        
        Args:
            event_types: List of event type IDs to filter
            start_time: Start time for event collection
            end_time: End time for event collection
            max_events: Maximum number of events to retrieve
            
        Returns:
            List of event dictionaries
        """
        self.logger.debug(f"Retrieving events: {event_types}")
        
        try:
            # Create event filter spec
            filter_spec = vim.event.EventFilterSpec()
            filter_spec.time = vim.event.EventFilterSpec.ByTime()
            filter_spec.time.beginTime = start_time
            filter_spec.time.endTime = end_time
            
            # Set event type filter
            if event_types:
                filter_spec.eventTypeId = event_types
            
            # Get event manager
            event_manager = self.content.eventManager
            
            # Create event collector
            collector = event_manager.CreateCollectorForEvents(filter_spec)
            
            events = []
            try:
                # Read events in batches
                while len(events) < max_events:
                    batch = collector.ReadNextEvents(100)
                    if not batch:
                        break
                    
                    for event in batch:
                        event_dict = self._event_to_dict(event)
                        events.append(event_dict)
                        
                        if len(events) >= max_events:
                            break
                
            finally:
                # Clean up collector
                collector.DestroyCollector()
            
            self.logger.info(f"Retrieved {len(events)} events")
            return events
            
        except Exception as e:
            self.logger.error(f"Error retrieving events: {str(e)}")
            return []
    
    def _event_to_dict(self, event: vim.event.Event) -> Dict[str, Any]:
        """
        Convert vCenter event object to dictionary.
        
        Args:
            event: vCenter event object
            
        Returns:
            Event dictionary
        """
        event_dict = {
            'key': event.key,
            'eventTypeId': event.__class__.__name__,
            'createdTime': event.createdTime,
            'userName': getattr(event, 'userName', None),
            'fullFormattedMessage': getattr(event, 'fullFormattedMessage', ''),
            'objectName': getattr(event, 'objectName', None),
            'objectType': getattr(event, 'objectType', None)
        }
        
        # Add VM information if available
        if hasattr(event, 'vm') and event.vm:
            event_dict['vm'] = {
                'name': event.vm.name,
                'moId': event.vm.vm._moId if hasattr(event.vm, 'vm') else None
            }
        
        # Add host information if available
        if hasattr(event, 'host') and event.host:
            event_dict['host'] = {
                'name': event.host.name,
                'moId': event.host.host._moId if hasattr(event.host, 'host') else None
            }
        
        # Add datacenter information if available
        if hasattr(event, 'datacenter') and event.datacenter:
            event_dict['datacenter'] = {
                'name': event.datacenter.name,
                'moId': event.datacenter.datacenter._moId if hasattr(event.datacenter, 'datacenter') else None
            }
        
        # Add DVS information if available
        if hasattr(event, 'dvs') and event.dvs:
            event_dict['dvs'] = {
                'name': event.dvs.name,
                'moId': event.dvs.dvs._moId if hasattr(event.dvs, 'dvs') else None
            }
        
        return event_dict
    
    def get_virtual_machines(self) -> List[Dict[str, Any]]:
        """
        Get list of virtual machines.
        
        Returns:
            List of VM dictionaries
        """
        self.logger.debug("Retrieving virtual machines")
        
        try:
            # Get VM container view
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder,
                [vim.VirtualMachine],
                True
            )
            
            vms = []
            for vm in container.view:
                vm_dict = {
                    'name': vm.name,
                    'moId': vm._moId,
                    'powerState': vm.runtime.powerState if vm.runtime else None,
                    'guestOS': vm.config.guestFullName if vm.config else None,
                    'numCPU': vm.config.hardware.numCPU if vm.config and vm.config.hardware else None,
                    'memoryMB': vm.config.hardware.memoryMB if vm.config and vm.config.hardware else None,
                    'host': vm.runtime.host.name if vm.runtime and vm.runtime.host else None
                }
                vms.append(vm_dict)
            
            try:
                container.Destroy()
            except Exception as cleanup_error:
                self.logger.warning(f"Error during cleanup: {str(cleanup_error)}")
            
            self.logger.info(f"Retrieved {len(vms)} virtual machines")
            return vms
            
        except Exception as e:
            self.logger.error(f"Error retrieving VMs: {str(e)}")
            return []
    
    def get_hosts(self) -> List[Dict[str, Any]]:
        """
        Get list of ESXi hosts.
        
        Returns:
            List of host dictionaries
        """
        self.logger.debug("Retrieving ESXi hosts")
        
        try:
            # Get host container view
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder,
                [vim.HostSystem],
                True
            )
            
            hosts = []
            for host in container.view:
                host_dict = {
                    'name': host.name,
                    'moId': host._moId,
                    'connectionState': host.runtime.connectionState if host.runtime else None,
                    'powerState': host.runtime.powerState if host.runtime else None,
                    'version': host.config.product.version if host.config and host.config.product else None,
                    'build': host.config.product.build if host.config and host.config.product else None,
                    'numCpuCores': host.hardware.cpuInfo.numCpuCores if host.hardware and host.hardware.cpuInfo else None,
                    'memorySize': host.hardware.memorySize if host.hardware else None
                }
                hosts.append(host_dict)
            
            container.Destroy()
            self.logger.info(f"Retrieved {len(hosts)} ESXi hosts")
            return hosts
            
        except Exception as e:
            self.logger.error(f"Error retrieving hosts: {str(e)}")
            return []
    
    def get_datacenters(self) -> List[Dict[str, Any]]:
        """
        Get list of datacenters.
        
        Returns:
            List of datacenter dictionaries
        """
        self.logger.debug("Retrieving datacenters")
        
        try:
            # Get datacenter container view
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder,
                [vim.Datacenter],
                True
            )
            
            datacenters = []
            for dc in container.view:
                dc_dict = {
                    'name': dc.name,
                    'moId': dc._moId
                }
                datacenters.append(dc_dict)
            
            container.Destroy()
            self.logger.info(f"Retrieved {len(datacenters)} datacenters")
            return datacenters
            
        except Exception as e:
            self.logger.error(f"Error retrieving datacenters: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test connection to vCenter.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if self.content:
                # Try to get session manager to test connection
                session_manager = self.content.sessionManager
                current_session = session_manager.currentSession
                
                if current_session:
                    self.logger.info("vCenter connection test successful")
                    return True
            
            self.logger.warning("vCenter connection test failed")
            return False
            
        except Exception as e:
            self.logger.error(f"vCenter connection test error: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        try:
            self.disconnect()
        except Exception as e:
            self.logger.warning(f"Error during context manager cleanup: {str(e)}")
        return False  # Don't suppress exceptions