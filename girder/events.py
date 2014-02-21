#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

"""
This module contains the Girder events framework. It maintains a global mapping
of events to listeners, and contains utilities for callers to handle or trigger
events identified by a name.
"""

import Queue
import threading

from .constants import TerminalColor


class Event(object):
    """
    An Event object is created when an event is triggered. It is passed to
    each of the listeners of the event, which have a chance to add information
    to the event, and also optionally stop the event from being further
    propagated to other listeners, and also optionally instruct the caller that
    it should not execute its default behavior.
    """

    # We might have a lot of events, so we use __slots__ to make them smaller
    __slots__ = (
        'info',
        'name',
        'propagate',
        'preventDefault',
        'responses'
    )

    def __init__(self, name, info):
        self.name = name
        self.info = info
        self.propagate = True
        self.preventDefault = False
        self.responses = []

    def preventDefault(self):
        """
        This can be used to instruct the triggerer of the event that the default
        behavior it would normally perform should not be performed. The
        semantics of this action are specific to the context of the event
        being handled, but a common use of this method is for a plugin to
        provide an alternate behavior that will replace the normal way the
        event is handled by the core system.
        """
        self.preventDefault = True

    def stopPropagation(self):
        """
        Listeners should call this on the event they were passed in order to
        stop any other listeners to the event from being executed.
        """
        self.propagate = False

    def addResponse(self, response):
        """
        Listeners that wish to return data back to the caller who triggered this
        event should call this to append their own response to the event.

        :param response: The response value, which can be any type.
        """
        self.responses.append(response)


class EventThread(threading.Thread):
    """
    This class is used to execute the pipeline for events asynchronously.
    This should not be invoked directly by callers; instead, they should use
    girder.events.triggerAsync().
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.terminate = False
        self.eventQueue = Queue.Queue()
        self.queueNotEmpty = threading.Condition()

    def run(self):
        """
        Loops over all queued events. If the queue is empty, this thread gets
        put to sleep until someone calls trigger() on it with a new event to
        dispatch.
        """
        print TerminalColor.info('Started asynchronous event manager thread.')

        while(not self.terminate):
            try:
                eventName, info = self.eventQueue.get(block=False)
                trigger(eventName, info)
            except Queue.Empty:
                self.queueNotEmpty.acquire()
                self.queueNotEmpty.wait()
                self.queueNotEmpty.release()

        print TerminalColor.info('Stopped asynchronous event manager thread.')

    def trigger(self, eventName, info=None):
        """
        Adds a new event on the queue to trigger asynchronously.

        :param eventName: The event name to pass to the girder.events.trigger
        :param info: The info object to pass to girder.events.trigger
        """
        self.queueNotEmpty.acquire()
        self.eventQueue.put((eventName, info))
        self.queueNotEmpty.notify()
        self.queueNotEmpty.release()

    def stop(self):
        """
        Gracefully stops this thread. Will finish the currently processing
        event before stopping.
        """
        self.queueNotEmpty.acquire()
        self.terminate = True
        self.queueNotEmpty.notify()
        self.queueNotEmpty.release()


def bind(eventName, handlerName, handler):
    """
    Bind a listener (handler) to the event identified by eventName. It is
    convention that plugins will use their own name as the handlerName, so that
    the trigger() caller can see which plugin(s) responded to the event.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param handlerName: The name that identifies the handler calling bind().
    :type handlerName: str
    :param handler: The function that will be called when the event is fired.
                    It must accept a single argument, which is the Event that
                    was created by trigger(). This function should not return
                    a value; any data that it needs to pass back to the
                    triggerer should be passed via the addResponse() method of
                    the Event.
    :type handler: function
    """
    global _mapping
    if not eventName in _mapping:
        _mapping[eventName] = []

    _mapping[eventName].append({
        'handlerName': handlerName,
        'handler': handler
    })


def unbind(eventName, handlerName):
    """
    Removes the binding between the event and the given listener.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param handlerName: The name that identifies the handler calling bind().
    :type handlerName: str
    """
    global _mapping
    for listener in _mapping.get(eventName, []):
        if listener['handlerName'] == handlerName:
            _mapping[eventName].remove(listener)


def trigger(eventName, info=None):
    """
    Fire an event with the given name. All listeners bound on that name will be
    called until they are exhausted or one of the handlers calls the
    stopPropagation() method on the event.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param info: The info argument to pass to the handler function. The type of
                 this argument is opaque, and can be anything.
    :return
    """
    global _mapping
    e = Event(eventName, info)
    for listener in _mapping.get(eventName, []):
        listener['handler'](e)
        if e.propagate is False:
            break

    return e


_mapping = {}
daemon = EventThread()
