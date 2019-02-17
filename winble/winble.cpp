#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <condition_variable>
#include <chrono>
#include <winrt/Windows.Devices.Bluetooth.h>
#include <winrt/Windows.Devices.Bluetooth.GenericAttributeProfile.h>
#include <winrt/Windows.Devices.Enumeration.h>
#include <winrt/Windows.Security.Cryptography.h>
#include <winrt/Windows.Storage.Streams.h>

// Link to umbrella lib.
#pragma comment(lib, "windowsapp")

using namespace winrt;
using namespace winrt::Windows::Devices::Enumeration;
using namespace winrt::Windows::Devices::Bluetooth;
using namespace winrt::Windows::Devices::Bluetooth::GenericAttributeProfile;
using namespace winrt::Windows::Security::Cryptography;
using namespace winrt::Windows::Storage::Streams;
namespace py = pybind11;

const std::vector<hstring> g_requestedProperties
{
    L"System.Devices.Aep.DeviceAddress",
    L"System.Devices.Aep.IsConnected",
    L"System.Devices.Aep.Bluetooth.Le.AddressType"
};

std::string GetDeviceAddress(const DeviceInformation& deviceInfo)
{
    return to_string(unbox_value<hstring>(deviceInfo.Properties().Lookup(L"System.Devices.Aep.DeviceAddress")));
}

uint64_t MacAddressStringToUint(std::string macAddress)
{
    // Remove colons if there are any
    macAddress.erase(std::remove(macAddress.begin(), macAddress.end(), ':'), macAddress.end());

    // Convert to uint64_t
    return strtoul(macAddress.c_str(), NULL, 16);
}

DeviceWatcher CreateDeviceWatcher()
{
    // We need to init the thread apartment before creating the watcher
    init_apartment();
    return DeviceInformation::CreateWatcher(
               //Windows::Devices::Bluetooth::BluetoothLEDevice::GetDeviceSelectorFromPairingState(false),
        BluetoothLEDevice::GetDeviceSelectorFromConnectionStatus(BluetoothConnectionStatus::Disconnected),
        g_requestedProperties,
        DeviceInformationKind::AssociationEndpoint
    );
}

guid BytesToGuid(const std::string& guidBytes)
{
    std::vector<uint8_t> guidVector(guidBytes.begin(), guidBytes.end());
    DataWriter guidWriter;
    guidWriter.WriteBytes(guidVector);
    DataReader guidReader = DataReader::FromBuffer(guidWriter.DetachBuffer());
    guid result{ guidReader.ReadGuid() };
    std::reverse(std::begin(result.Data4), std::end(result.Data4));
    return result;
}

std::vector<GattCharacteristic> GetCharacteristics(const BluetoothLEDevice& device)
{
    std::vector<GattCharacteristic> allCharacteristics;

    GattDeviceServicesResult getServicesResult
    {
        device.GetGattServicesAsync(BluetoothCacheMode::Uncached).get()
    };

    if (getServicesResult.Status() != GattCommunicationStatus::Success)
    {
        throw std::exception();
    }

    auto services = getServicesResult.Services();
    for (const auto& service : services)
    {
        GattCharacteristicsResult characteristicsResult
        {
            service.GetCharacteristicsAsync(BluetoothCacheMode::Uncached).get()
        };

        if (characteristicsResult.Status() != GattCommunicationStatus::Success)
        {
            throw std::exception();
        }

        auto characterisitcs = characteristicsResult.Characteristics();
        allCharacteristics.insert(allCharacteristics.end(), begin(characterisitcs), end(characterisitcs));
    }

    return allCharacteristics;
}

struct WinBleDevice
{
    WinBleDevice(BluetoothLEDevice&& device)
        : m_device{ std::move(device) }
        // NOTE: Getting all characteristics only seems to work
        // in the constructor.
        // This probably has something to do with needing to be on the UI thread.
        , m_characteristics{ GetCharacteristics(m_device) }
    {
    }

    void WriteToCharacteristic(std::string characteristicId, std::string data)
    {
        DataWriter writer;
        std::vector<uint8_t> dataBytes(data.cbegin(), data.cend());
        writer.WriteBytes(dataBytes);

        guid characteristicGuid{ BytesToGuid(characteristicId) };
        auto characteristicItr = std::find_if(m_characteristics.begin(), m_characteristics.end(),
            [&characteristicGuid](const GattCharacteristic& characteristic)
            {
                return characteristicGuid == characteristic.Uuid();
            }
        );

        if (characteristicItr == m_characteristics.end())
        {
            throw std::exception();
        }

        // Assume for now that we only got one characteristic.
        GattCommunicationStatus result
        {
            characteristicItr->WriteValueAsync(writer.DetachBuffer()).get()
        };

        if (result != GattCommunicationStatus::Success)
        {
            throw std::exception("WinBleDevice: Error sending data to bluetooth device.", static_cast<int>(result));
        }
    }

    void Subscribe(std::string characteristicId, const std::function<void(py::bytes)>& eventHandler)
    {
        if (!eventHandler) { return; }

        guid characteristicGuid{ BytesToGuid(characteristicId) };
        auto characteristicItr = std::find_if(m_characteristics.begin(), m_characteristics.end(),
            [&characteristicGuid](const GattCharacteristic& characteristic)
            {
                return characteristicGuid == characteristic.Uuid();
            }
        );

        if (characteristicItr == m_characteristics.end())
        {
            throw std::exception();
        }

        // Tell the characteristic we want to receive notifications.
        GattCommunicationStatus status
        {
            characteristicItr->WriteClientCharacteristicConfigurationDescriptorAsync(
                GattClientCharacteristicConfigurationDescriptorValue::Notify
            ).get()
        };

        if (status != GattCommunicationStatus::Success)
        {
            throw std::exception();
        }

        event_token valueChangedEventToken = characteristicItr->ValueChanged(
            [eventHandler](
                GattCharacteristic,
                GattValueChangedEventArgs valueChangedEventArgs
            )
            {
                // Use https://github.com/Microsoft/Windows-universal-samples/blob/master/Samples/BluetoothLE/cs/Scenario2_Client.xaml.cs
                // As an example.
                com_array<uint8_t> data;
                CryptographicBuffer::CopyToByteArray(valueChangedEventArgs.CharacteristicValue(), data);
                std::string dataAsString{ data.begin(), data.end() };
                py::bytes dataAsPyType{ dataAsString };
                eventHandler(dataAsPyType);
            }
        );
    }

    void Disconnect()
    {
        m_device.Close();
    }

private:
    BluetoothLEDevice m_device;
    // In-memory cache of characteristics from the device.
    std::vector<GattCharacteristic> m_characteristics;
};

struct WinBleAdapter
{
    WinBleAdapter()
        : m_deviceWatcher{ CreateDeviceWatcher() }
    {
        init_apartment();
    }

    ~WinBleAdapter()
    {
        m_deviceWatcher.Stop();
        uninit_apartment();
    }

    void Start()
    {
        // Do nothing if the watcher is already started.
        if (m_deviceWatcher.Status() == Windows::Devices::Enumeration::DeviceWatcherStatus::Started)
        {
            return;
        }

        // Register event handlers before starting the watcher.
        // Added, Updated and Removed are required to get all nearby devices
        m_addedEventToken = m_deviceWatcher.Added(
            [this](
                const Windows::Devices::Enumeration::DeviceWatcher&,
                const Windows::Devices::Enumeration::DeviceInformation& deviceInfo
            )
            {
                m_nearbyDevices.insert(deviceInfo);
            }
        );

        m_updatedEventToken = m_deviceWatcher.Updated(
            [this](
                const Windows::Devices::Enumeration::DeviceWatcher&,
                const Windows::Devices::Enumeration::DeviceInformationUpdate& deviceInfoUpdate
            )
            {
                auto foundDeviceInfoItr = std::find_if(m_nearbyDevices.cbegin(), m_nearbyDevices.cend(),
                    [&deviceInfoUpdate](
                        const Windows::Devices::Enumeration::DeviceInformation& deviceInfo
                    ) -> bool
                    {
                        return deviceInfo.Id() == deviceInfoUpdate.Id();
                    }
                );

                if (foundDeviceInfoItr != m_nearbyDevices.cend())
                {
                    foundDeviceInfoItr->Update(deviceInfoUpdate);
                }
            }
        );

        m_removedEventToken = m_deviceWatcher.Removed(
            [this](
                const Windows::Devices::Enumeration::DeviceWatcher&,
                const Windows::Devices::Enumeration::DeviceInformationUpdate& deviceInfoUpdate
            )
            {
                m_nearbyDevices.erase(
                    std::find_if(m_nearbyDevices.begin(), m_nearbyDevices.end(),
                        [&deviceInfoUpdate](
                            const Windows::Devices::Enumeration::DeviceInformation& deviceInfo
                        ) -> bool
                        {
                            return deviceInfo.Id() == deviceInfoUpdate.Id();
                        }
                    )
                );
            }
        );

        m_deviceEunumerationCompletedEventToken = m_deviceWatcher.EnumerationCompleted(
            [this](
                const Windows::Devices::Enumeration::DeviceWatcher& deviceWatcher,
                const Windows::Foundation::IInspectable&
            )
            {
                m_enumerationCompletedEvent.notify_all();
            }
        );

        m_deviceWatcher.Start();
    }

    py::list Scan()
    {
        // Wait for device enumeration to complete.
        std::mutex m;
        std::unique_lock<std::mutex> lock{ m };
        /*auto now = std::chrono::system_clock::now();
        using namespace std::chrono_literals;
        enumerationCompletedEvent.wait_until(lock, now + 20s);*/
        m_enumerationCompletedEvent.wait(lock);

        // TODO: lock for m_nearbyDevices
        py::list devices;
        for (const auto& deviceInfo : m_nearbyDevices)
        {
            py::dict device;
            device["name"] = to_string(deviceInfo.Name());
            device["address"] = GetDeviceAddress(deviceInfo);
            devices.append(device);
        }

        return devices;
    }

    WinBleDevice Connect(std::string address)
    {
        auto deviceInfoItr = std::find_if(m_nearbyDevices.cbegin(), m_nearbyDevices.cend(),
            [&address](const Windows::Devices::Enumeration::DeviceInformation& deviceInfo) -> bool
            {
                return GetDeviceAddress(deviceInfo) == address;
            }
        );

        if (deviceInfoItr != m_nearbyDevices.cend())
        {
            Windows::Devices::Bluetooth::BluetoothLEDevice device
            {
                Windows::Devices::Bluetooth::BluetoothLEDevice::FromIdAsync(deviceInfoItr->Id()).get()
            };

            return { std::move(device) };
        }
        else
        {
            Windows::Devices::Bluetooth::BluetoothLEDevice device
            {
                Windows::Devices::Bluetooth::BluetoothLEDevice::FromBluetoothAddressAsync(MacAddressStringToUint(address)).get()
            };

            return { std::move(device) };
        }
    }

private:
    Windows::Devices::Enumeration::DeviceWatcher m_deviceWatcher;
    std::unordered_set<Windows::Devices::Enumeration::DeviceInformation> m_nearbyDevices;
    std::condition_variable m_enumerationCompletedEvent;
    event_token m_addedEventToken;
    event_token m_updatedEventToken;
    event_token m_removedEventToken;
    event_token m_deviceEunumerationCompletedEventToken;
};

PYBIND11_MODULE(winble, m)
{
    py::class_<WinBleAdapter>(m, "WinBleAdapter")
        .def(py::init<>())
        .def("start", &WinBleAdapter::Start)
        .def("scan", &WinBleAdapter::Scan)
        .def("connect", &WinBleAdapter::Connect);

    py::class_<WinBleDevice>(m, "WinBleDevice")
        .def("char_write", &WinBleDevice::WriteToCharacteristic)
        .def("subscribe", &WinBleDevice::Subscribe)
        .def("disconnect", &WinBleDevice::Disconnect);

    m.doc() = "Windows BLE Library";

#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}

