# Third-party
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
            enabledLayerCount = 0,
            enabledExtensionCount = len(self.extensions),
            ppEnabledExtensionNames = self.extensions)
        
        self._instance = vkCreateInstance(self.instance_info, None)
        if self._instance == None:
            raise RuntimeError("Could not create Vulkan instance")

        # physical device selection
        self._physical_device = None
        physical_devices = vkEnumeratePhysicalDevices(self._instance)
        # a filter function would probably be more pythonic here
        for device in physical_devices:
            family = vkGetPhysicalDeviceQueueFamilyProperties(device)
            for graphics_family, prop in enumerate(family):
                if prop.queueCount > 0:
                    if prop.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                        self._physical_device = device
                        break
        # seems like a good place for a 'for: else:', but inverted somehow?
        if self._physical_device == None:
            raise RuntimeError("Could not find suitable physical device")
        # ^^^ FILTHY DIRTY ^^^ (far from pythonic)

        q_create_info = VkDeviceQueueCreateInfo(
            queueFamilyIndex = graphics_family, # collected above
            queueCount = 1,
            pQueuePriorities = [1.0])

        d_create_info = VkDeviceCreateInfo(
            queueCreateInfoCount = 1,
            pQueueCreateInfos = q_create_info,
            enabledExtensionCount = 0,
            enabledLayerCount = 0,
            pEnabledFeatures = VkPhysicalDeviceFeatures())

        self._device = vkCreateDevice(self._physical_device, d_create_info, None)
        # ^ NOT physical device! (distinction unknown)

##        self._graphic_queue = vkGetDeviceQueue(self._device, graphics_family, 0)
##        self._present_queue = vkGetDeviceQueue(self._device, graphics_family, 0)

    def __del__(self):
        if self._instance != None:
            vkDestroyInstance(self._instance, None)


if __name__ == "__main__":
    import sys

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook
    
    # APPLICATION
    app = QtWidgets.QApplication([])
    window = VulkanWindow() # not executing?
    window.show()

    def cleanup():
        global window
        del window
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec_())
    sys.stdout.close()
