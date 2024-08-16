#!/usr/bin/env python3
# encoding: utf-8

import cv2

from map_configurator.map_configurator import configureSensorAndMapPosition
from map_configurator.map_propagator import propagateHeatmaps


if __name__ == "__main__":
    # configureSensorAndMapPosition()
    propagateHeatmaps()
    cv2.destroyAllWindows()