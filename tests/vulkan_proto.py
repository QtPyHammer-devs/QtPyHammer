import sys
# Third-party
from cffi import FFI
from PyQt5 import QtGui, QtWidgets
from vulkan import *


class VulkanWindow(QtWidgets.QWidget):
    def __init__(self):
        super(VulkanWindow, self).__init__()
        self.setWindowTitle("Vulkan Test")
        self.setMinimumSize(720, 576)

        # initialize Vulkan
        self.app_info = VkApplicationInfo(
            pApplicationName = "Python VK",
            applicationVersion = VK_MAKE_VERSION(1, 0, 0),
            pEngineName = "pyvulkan",
            engineVersion=VK_MAKE_VERSION(1, 0, 0),
            apiVersion=VK_API_VERSION)
        
        self.extensions = [ext.extensionName for ext in
                      vkEnumerateInstanceExtensionProperties(None)]
        
        self.instance_info = VkInstanceCreateInfo(
            pApplicationInfo = self.app_info,
            enabledLayerCount = 0, # validation layers
            enabledExtensionCount = len(self.extensions),
            ppEnabledExtensionNames = self.extensions)
        
        self._instance = vkCreateInstance(self.instance_info, None)
        if self._instance == None:
            raise RuntimeError("Could not create Vulkan instance")

        # DEBUG CALLBACK GOES HERE

        # surface creation
        if sys.platform == "win32":
            c_intf = FFI() # get the hInstance of the current window
            c_intf.cdef("long __stdcall GetWindowLongA(void* hWnd, int nIndex);")
            lib = c_intf.dlopen("User32.dll") # get C funtion from this .dll
            s_create_info = VkWin32SurfaceCreateInfoKHR(
                hwnd = self.winId(),
                hinstance = lib.GetWindowLongA(c_intf.cast("void*", self.winId()), -6))
            createSurface = self.getInstanceProc("vkCreateWin32SurfaceKHR")
        elif sys.platform == "linux":
            VkWaylandSurfaceCreateInfoKHR()
        self._surface = createSurface(self._instance, s_create_info, None)

##        # physical device selection
##        self._physical_device = None
##        physical_devices = vkEnumeratePhysicalDevices(self._instance)
##
##        for device in physical_devices:
##            family = vkGetPhysicalDeviceQueueFamilyProperties(device)
##            
##            for graphics_family, prop in enumerate(family):
##                if prop.queueCount > 0:
##                    if prop.queueFlags & VK_QUEUE_GRAPHICS_BIT:
##                        self._physical_device = device
##                    surface_supported = self.getInstanceProc("vkGetPhysicalDeviceSurfaceSupportKHR")
##                    
##                    if surface_supported(device, graphics_family, self._surface):
##                        ...:
##
##        if self._physical_device == None:
##            raise RuntimeError("Could not find suitable physical device")
##
##        # logical device creation
##        q_create_infos = []
##        for ? in ?:
##            o = VkDeviceQueueCreateInfo(
##                queueFamilyIndex = graphics_family,
##                queueCount = 1,
##                pQueuePriorities = [1.0])
##
##        d_create_info = VkDeviceCreateInfo(
##            queueCreateInfoCount = len(q_create_infos),
##            pQueueCreateInfos = q_create_infos,
##            enabledExtensionCount = 0,
##            enabledLayerCount = 0, # validation layers
##            pEnabledFeatures = VkPhysicalDeviceFeatures())
##
##        self._device = vkCreateDevice(self._physical_device, d_create_info, None)

    def __del__(self):
##        if self._surface != None:
##            vkDestroySurfaceKHR(self._instance, self._surface, None)
##        if self._device != None:
##            vkDestroyDevice(self._device, None)
        if self._instance != None:
            vkDestroyInstance(self._instance, None)

    def getInstanceProc(self, function_name): # returns function
        return vkGetInstanceProcAddr(self._instance, function_name)


if __name__ == "__main__":
    import sys

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook
    
    # APPLICATION
    app = QtWidgets.QApplication([])
    window = VulkanWindow()
    window.show()

    def cleanup():
        global window
        del window
    
    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec_())
