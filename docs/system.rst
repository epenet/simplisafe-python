Systems
=======

:meth:`System <simplipy.system.System>` objects are used to retrieve data on and control the state
of SimpliSafe™ systems. Two types of objects can be returned:

* :meth:`SystemV2 <simplipy.system.v2.SystemV2>`: an object to control V2 (classic)
  SimpliSafe™ systems
* :meth:`SystemV3 <simplipy.system.v3.SystemV3>`: an object to control V3 (new, released
  in 2018) SimpliSafe™ systems

Despite the differences, ``simplipy`` provides a common interface to
these objects, meaning many of the same properties and methods are available to
both.

To get all SimpliSafe™ systems associated with an account:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            api = await simplipy.API.async_from_auth(
                "<AUTHORIZATION_CODE>",
                "<CODE_VERIFIER>",
                session=session,
            )

            # Get a dict of systems with the system ID as the key:
            systems = await api.async_get_systems()
            # >>> {"1234abc": <simplipy.system.SystemV2 object>, ...}


    asyncio.run(main())

Core Properties
---------------

All :meth:`System <simplipy.system.System>` objects come with a standard set of
properties:

.. code:: python

    # Return the street address of the system:
    system.address
    # >>> 1234 Main Street

    # Return whether the alarm is currently going off:
    system.alarm_going_off
    # >>> False

    # Return the type of connection the system is using:
    system.connection_type
    # >>> "cell"

    # Return a list of active notifications:
    system.notifications
    # >>> [<simplipy.system.SystemNotification object>, ...]

    # Return a list of sensors attached to this system
    # (detailed later):
    system.sensors
    # >>> [<simplipy.sensor.SensorV2 object>, ...]

    # Return the system's serial number:
    system.serial
    # >>> xxxxxxxxxxxxxx

    # Return the current state of the system:
    system.state
    # >>> simplipy.system.SystemStates.AWAY

    # Return the SimpliSafe™ identifier for this system
    # from the key:
    system_id
    # >>> 1234abc

    # ...or as a property of the system itself:
    system.system_id
    # >>> 1234abc

    # Return the average of all temperature sensors
    # (if they exist):
    system.temperature
    # >>> 67

    # Return the SimpliSafe™ version:
    system.version
    # >>> 2

V3 Properties
-------------

If a :meth:`System <simplipy.system.v3.SystemV3>` object should be a V3 system, it will
automatically come with additional properties:

.. code:: python

    # Return the number of seconds an activated alarm
    # will sound for:
    system.alarm_duration
    # >>> 240

    # Return the loudness of the alarm volume:
    system.alarm_volume
    # >>> 3

    # Return the power rating of the battery backup:
    system.battery_backup_power_level
    # >>> 5239

    # Return the number of seconds to delay when returning
    # to an "away" alarm:
    system.entry_delay_away
    # >>> 30

    # Return the number of seconds to delay when returning
    # to an "home" alarm:
    system.entry_delay_home
    # >>> 30

    # Return the number of seconds to delay when exiting
    # an "away" alarm:
    system.exit_delay_away
    # >>> 60

    # Return the number of seconds to delay when exiting
    # an "home" alarm:
    system.exit_delay_home
    # >>> 0

    # Return the signal strength of the cell antenna:
    system.gsm_strength
    # >>> -73

    # Return whether the base station light is on:
    system.light
    # >>> True

     # Return any active system messages/notifications
    system.notifications
    # >>> [Message(...)]

    # Return whether the system is offline:
    system.offline
    # >>> False

    # Return whether the system is experiencing a power
    # outage:
    system.power_outage
    # >>> False

    # Return whether the base station is noticing RF jamming:
    system.rf_jamming
    # >>> False

    # Return the loudness of the voice prompt:
    system.voice_prompt_volume
    # >>> 2

    # Return the power rating of the A/C outlet:
    system.wall_power_level
    # >>> 5239

    # Return the ssid of the base station:
    system.wifi_ssid
    # >>> "My_SSID"

    # Return the signal strength of the wifi antenna:
    system.wifi_strength
    # >>> -43

V3 systems also come with a :meth:`async_set_properties <simplipy.system.v3.SystemV3.async_set_properties>`
method to update the following system properties:

* ``alarm_duration`` (in seconds): 30-480
* ``alarm_volume``: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH
* ``chime_volume``: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH
* ``entry_delay_away`` (in seconds): 30-255
* ``entry_delay_home`` (in seconds): 0-255
* ``exit_delay_away`` (in seconds): 45-255
* ``exit_delay_home`` (in seconds): 0-255
* ``light``: True or False
* ``voice_prompt_volume``: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH

Note that the ``simplipy.system.v3.Volume`` enum class should be used for volume
properties.

.. code:: python

    from simplipy.system.v3 import Volume

    await system.async_set_properties(
        {
            "alarm_duration": 240,
            "alarm_volume": Volume.HIGH,
            "chime_volume": Volume.MEDIUM,
            "entry_delay_away": 30,
            "entry_delay_home": 30,
            "exit_delay_away": 60,
            "exit_delay_home": 0,
            "light": True,
            "voice_prompt_volume": Volume.MEDIUM,
        }
    )

Attempting to call these coroutines with a value beyond these limits will raise a
:meth:`SimplipyError <simplipy.errors.SimplipyError>`.

Updating the System
-------------------

Refreshing the :meth:`System <simplipy.system.System>` object is done via the
:meth:`update() <simplipy.system.System.update>` coroutine:

.. code:: python

    await system.async_update()

Note that this method can be supplied with four optional parameters (all of which
default to ``True``):

* ``include_system``: update the system state and properties
* ``include_settings``: update system settings (like PINs)
* ``include_entities``: update all sensors/locks/etc. associated with a system
* ``cached``: use the last values provides by the base station

For instance, if a user only wanted to update sensors and wanted to force a new data
refresh:

.. code:: python

    await system.async_update(include_system=False, include_settings=False, cached=False)

There are two crucial differences between V2 and V3 systems when updating:

* V2 systems, which use only 2G cell connectivity, will be slower to update
  than V3 systems when those V3 systems are connected to WiFi.
* V2 systems will audibly announce, "Your settings have been synchronized."
  when the update completes; V3 systems will not. Unfortunately, this cannot
  currently be worked around.

Arming/Disarming
----------------

Arming the system in home/away mode and disarming the system are done via a set
of three coroutines:

.. code:: python

    await system.async_set_away()
    await system.async_set_home()
    await system.async_set_off()


Events
------

The :meth:`System <simplipy.system.System>` object allows users to view events that have
occurred with their system:

.. code:: python

   from datetime import datetime, timedelta

   yesterday = datetime.now() - timedelta(days=1)
    await system.async_get_events(
        from_timestamp=yesterday, num_events=2
    )
    # >>> [{"eventId": 123, ...}, {"eventId": 456, ...}]

    await system.async_get_latest_event()
    # >>> {"eventId": 987, ...}

System Notifications
--------------------

The ``notifications`` property of the :meth:`System <simplipy.system.System>` object
contains any active system notifications (in the form of
:meth:`SystemNotification <simplipy.system.SystemNotification>` objects).

Notifications remain within ``system.notifications`` until cleared, which can be
accomplished by:

1. Manually clearing them in the SimpliSafe™ web and mobile applications
2. Using the :meth:`system.clear_notifications <simplipy.system.System.clear_notifications>`
   coroutine.

PINs
----

``simplipy`` allows users to easily retrieve, set, reset, and remove PINs
associated with a SimpliSafe™ account:

.. code:: python

    # Get all PINs (retrieving fresh or from the cache):
    await system.async_get_pins(cached=False)
    # >>> {"master": "1234", "duress": "9876"}

    # Set a new user PIN:
    await system.async_set_pin("My New User", "1122")
    await system.async_get_pins(cached=False)
    # >>> {"master": "1234", "duress": "9876", "My New User": "1122"}

    # Remove a PIN (by value or by label)
    await system.async_remove_pin("My New User")
    await system.async_get_pins(cached=False)
    # >>> {"master": "1234", "duress": "9876"}

    # Set the master PIN (works for the duress PIN, too):
    await system.async_set_pin("master", "9865")
    await system.async_get_pins(cached=False)
    # >>> {"master": "9865", "duress": "9876"}

Remember that with V2 systems, many operations – including setting PINs – will cause
the base station to audibly announce "Your settings have been synchronized."
