# NOTES:
# https://renderdoc.org/vulkan-in-30-minutes.html
# https://github.com/LunarG/VulkanSamples
# https://github.com/mackst/vulkan-tutorial
# https://vulkan.lunarg.com/doc/sdk/1.2.135.0/windows/tutorial/html/index.html

import sys
# Third-party
from cffi import FFI
from sdl2 import *
from vulkan import *


def main(width=720, height=576):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b"Vulkan Test - SDL2",
                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              width, height,
                              SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    app_info = VkApplicationInfo(
        pApplicationName = "Python VK",
        applicationVersion = VK_MAKE_VERSION(1, 0, 0),
        pEngineName = "pyvulkan",
        engineVersion=VK_MAKE_VERSION(1, 0, 0),
        apiVersion=VK_API_VERSION)
        
    extensions = [ext.extensionName for ext in vkEnumerateInstanceExtensionProperties(None)]
        
    instance_info = VkInstanceCreateInfo(
        pApplicationInfo = app_info,
        enabledLayerCount = 0, # validation layers
        enabledExtensionCount = len(extensions),
        ppEnabledExtensionNames = extensions)
        
    vk_instance = vkCreateInstance(instance_info, None)
    if vk_instance == None:
        raise RuntimeError("Could not create Vulkan instance")

    def getInstanceProc(function_name):
        return vkGetInstanceProcAddr(vk_instance, function_name)

    # DEBUG CALLBACK GOES HERE

    # surface creation
    if sys.platform == "win32":
        wminfo = SDL_SysWMinfo
        print(dir(window))
        SDL_VERSION(wminfo.version)
        hwnd = SDL_GetWindowWMInfo(window, wminfo).info.win.window
        
        c_intf = FFI() # get the hInstance of the current window
        c_intf.cdef("long __stdcall GetWindowLongA(void* hWnd, int nIndex);")
        lib = c_intf.dlopen("User32.dll") # get C funtion from this .dll
        hinstance = lib.GetWindowLongA(c_intf.cast("void*", hwnd), -6)
        s_create_info = VkWin32SurfaceCreateInfoKHR(
            hwnd = hwnd,
            hinstance = hinstance)
        createSurface = getInstanceProc("vkCreateWin32SurfaceKHR")
    else:
        raise NotImplementedError("Cannont create surface on this platform")
    vk_surface = createSurface(vk_instance, s_create_info, None)

    # physical device (GPU) selection
    vk_physical_device = None
    present_family = None
    physical_devices = vkEnumeratePhysicalDevices(vk_instance)
    surfaceSupported = getInstanceProc("vkGetPhysicalDeviceSurfaceSupportKHR")
    for device in physical_devices:
        family = vkGetPhysicalDeviceQueueFamilyProperties(device)
        for graphics_family, prop in enumerate(family):
            if prop.queueCount > 0:
                if prop.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                    vk_physical_device = device
                if surfaceSupported(device, graphics_family, vk_surface):
                    # doesn't need to be same as physical device, but can be
                    present_family = graphics_family
                if vk_physical_device != None and present_family != None:
                    break
    if vk_physical_device == None:
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

    vk_device = vkCreateDevice(vk_physical_device, d_create_info, None)

    def getDeviceProc(self, function_name):
        return vkGetDeviceProcAddr(vk_device, function_name)

    vk_graphics_queue = vkGetDeviceQueue(vk_device, graphics_family, 0)
    vk_present_queue = vkGetDeviceQueue(vk_device, present_family, 0)

    ## SWAP CHAIN       
    # surface formatting
    surfaceFormats = getInstanceProc("vkGetPhysicalDeviceSurfaceFormatsKHR")
    surface_formats = surfaceFormats(vk_physical_device, vk_surface)
    if surface_formats[0].format == VK_FORMAT_UNDEFINED:
        chosen_format = [VK_FORMAT_B8G8R8A8_UNORM, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR]
    else:              # ^ format, colorSpace
        chosen_format = surface_formats[0]
    
    surfaceCapabilities = getInstanceProc("vkGetPhysicalDeviceSurfaceCapabilitiesKHR")
    surface_capabilities = surfaceCapabilities(vk_physical_device, vk_surface)

    image_count = surface_capabilities.minImageCount + 1
    if 0 < surface_capabilities.maxImageCount < image_count:
        image_count = surface_capabilities.maxImageCount
    
    # render target extents
    max_bounds = surface_capabilities.maxImageExtent
    min_bounds = surface_capabilities.minImageExtent
    width = max(max_bounds.width, min(min_bounds.width, width))
    height = max(max_bounds.height, min(min_bounds.height, height))
    extents = VkExtent2D(width, height)        

    # present mode
    surfacePresentModes = getInstanceProc("vkGetPhysicalDeviceSurfacePresentModesKHR")
    surface_present_modes = surfacePresentModes(vk_physical_device, vk_surface)
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
        surface = vk_surface,
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

##    createSwapchain = getInstanceProc("vkCreateSwapchainKHR")
##    vk_swap_chain = createSwapchain(vk_device, sc_create_info, None) # CRASHES?
##    if vk_swap_chain == None:
##        raise RuntimeError("Could not create Swapchain")
##
##    getSwapchainImages = getInstanceProc("vkGetSwapchainImagesKHR")
##    vk_swap_chain_images = getSwapchainImages(vk_device, vk_swap_chain)
##    # note imageformat and extent

    # teardown
    if vk_surface != None:
        destroySurface = getInstanceProc("vkDestroySurfaceKHR")
        destroySurface(vkinstance, vk_surface, None)
    if vk_device != None:
        vkDestroyDevice(vk_device, None)
    if vk_instance != None:
        vkDestroyInstance(vk_instance, None)

    SDL_QUIT()


if __name__ == "__main__":
    main()
