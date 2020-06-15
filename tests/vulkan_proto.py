# NOTES:
# https://renderdoc.org/vulkan-in-30-minutes.html
# https://github.com/LunarG/VulkanSamples
# https://github.com/mackst/vulkan-tutorial
# https://vulkan.lunarg.com/doc/sdk/1.2.135.0/windows/tutorial/html/index.html

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
        # ^ returns VkErrorIncompatibleDriver on linux laptop
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
            # we take our example from
            # https://github.com/qt/qtwayland/blob/5832b6628d848b271efae99585206fa02fc214c9/src/client/qwaylandvulkaninstance.cpp#L108
            s_create_info = VkWaylandSurfaceCreateInfoKHR(
                display = self.display().wl_display(),
                surface = self.wlSurface())
            createSurface = self.getInstanceProc("vkCreateWaylandSurfaceKHR") # untested / linux machine broke
        self._surface = createSurface(self._instance, s_create_info, None)

        # physical device (GPU) selection
        self._physical_device = None
        present_family = None
        physical_devices = vkEnumeratePhysicalDevices(self._instance)
        surfaceSupported = self.getInstanceProc("vkGetPhysicalDeviceSurfaceSupportKHR")
        for device in physical_devices:
            family = vkGetPhysicalDeviceQueueFamilyProperties(device)
            for graphics_family, prop in enumerate(family):
                if prop.queueCount > 0:
                    if prop.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                        self._physical_device = device
                    if surfaceSupported(device, graphics_family, self._surface):
                        # doesn't need to be same as physical device, but can be
                        present_family = graphics_family
                    if self._physical_device != None and present_family != None:
                        break
        if self._physical_device == None:
            raise RuntimeError("Could not find suitable physical device")

        # logical device creation (similar to GL context)
        queue_families = set((graphics_family, present_family))
        q_create_infos = []
        for family in queue_families:
            qci = VkDeviceQueueCreateInfo(
                queueFamilyIndex = family,
                queueCount = 1,
                pQueuePriorities = [1.0])
            q_create_infos.append(qci)

        d_create_info = VkDeviceCreateInfo(
            queueCreateInfoCount = len(q_create_infos),
            pQueueCreateInfos = q_create_infos,
            enabledExtensionCount = 0,
            enabledLayerCount = 0, # validation layers
            pEnabledFeatures = VkPhysicalDeviceFeatures())

        self._device = vkCreateDevice(self._physical_device, d_create_info, None)

        self._graphics_queue = vkGetDeviceQueue(self._device, graphics_family, 0)
        self._present_queue = vkGetDeviceQueue(self._device, present_family, 0)

        ## SWAP CHAIN       
        # surface formatting
        surfaceFormats = self.getInstanceProc("vkGetPhysicalDeviceSurfaceFormatsKHR")
        surface_formats = surfaceFormats(self._physical_device, self._surface)
        if surface_formats[0].format == VK_FORMAT_UNDEFINED:
            chosen_format = [VK_FORMAT_B8G8R8A8_UNORM, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR]
        else:              # ^ format, colorSpace
            chosen_format = surface_formats[0]
        
        surfaceCapabilities = self.getInstanceProc("vkGetPhysicalDeviceSurfaceCapabilitiesKHR")
        surface_capabilities = surfaceCapabilities(self._physical_device, self._surface)

        image_count = surface_capabilities.minImageCount + 1
        if 0 < surface_capabilities.maxImageCount < image_count:
            image_count = surface_capabilities.maxImageCount
        
        # render target extents
        max_bounds = surface_capabilities.maxImageExtent
        min_bounds = surface_capabilities.minImageExtent
        width = max(max_bounds.width, min(min_bounds.width, self.width()))
        height = max(max_bounds.height, min(min_bounds.height, self.height()))
        extents = VkExtent2D(width, height)        

        # present mode
        surfacePresentModes = self.getInstanceProc("vkGetPhysicalDeviceSurfacePresentModesKHR")
        surface_present_modes = surfacePresentModes(self._physical_device, self._surface)
        desired_modes = [VK_PRESENT_MODE_FIFO_KHR,
            VK_PRESENT_MODE_MAILBOX_KHR,
            VK_PRESENT_MODE_IMMEDIATE_KHR]
        for mode in desired_modes:
            if mode in surface_present_modes:
                present_mode = mode
                break
        else:
            present_mode = surface_present_modes[0]

        sc_create_info = VkSwapchainCreateInfoKHR(
            surface = self._surface,
            minImageCount = image_count,
            imageFormat = chosen_format.colorSpace,
            imageExtent = extents,
            imageArrayLayers = 1,
            imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
            queueFamilyIndexCount = len(queue_families),
            pQueueFamilyIndices = tuple(queue_families),
            imageSharingMode = VK_SHARING_MODE_CONCURRENT,
            preTransform = surface_capabilities.currentTransform,
            compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
            presentMode = present_mode,
            clipped = True)
        if len(queue_families) == 1:
            sc_create_info.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE

        # STILL NEED TO MAKE MORE COMPATABILITY CHECKS WITH DEVICES
        # surface supported by vkGetPhysicalDeviceSurfaceSupportKHR (present_family)

##        createSwapchain = self.getInstanceProc("vkCreateSwapchainKHR")
##        self._swap_chain = createSwapchain(self._device, sc_create_info, None) # CRASHES?
##        if self._swap_chain == None:
##            raise RuntimeError("Could not create Swapchain")
##
##        getSwapchainImages = self.getInstanceProc("vkGetSwapchainImagesKHR")
##        self._swap_chain_images = getSwapchainImages(self._device, self._swap_chain)
##        # note imageformat and extent

    def __del__(self):
        if self._surface != None:
            destroySurface = self.getInstanceProc("vkDestroySurfaceKHR")
            destroySurface(self._instance, self._surface, None)
        if self._device != None:
            vkDestroyDevice(self._device, None)
        if self._instance != None:
            vkDestroyInstance(self._instance, None)

    def getInstanceProc(self, function_name): # returns function
        """think ARB or EXT"""
        return vkGetInstanceProcAddr(self._instance, function_name)

    def getDeviceProc(self, function_name):
        return vkGetDeviceProcAddr(self._device, function_name)


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
