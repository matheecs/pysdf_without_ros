class Quaternion:
    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0):
        """
        Constructor for Quaternion class.

        Parameters:
            x (float): The x component of the quaternion.
            y (float): The y component of the quaternion.
            z (float): The z component of the quaternion.
            w (float): The w component of the quaternion.
        """
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __str__(self):
        """
        String representation of the Quaternion object.
        """
        return f"Quaternion: ({self.x}, {self.y}, {self.z}, {self.w})"


class Point:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        """
        Constructor for Point class.

        Parameters:
            x (float): The x coordinate of the point.
            y (float): The y coordinate of the point.
            z (float): The z coordinate of the point.
        """
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        """
        String representation of the Point object.
        """
        return f"Point: ({self.x}, {self.y}, {self.z})"


class Pose:
    def __init__(self, position=None, orientation=None):
        """
        Constructor for Pose class.

        Parameters:
            position (geometry_msgs.msg.Point): The position of the object.
            orientation (geometry_msgs.msg.Quaternion): The orientation of the object.
        """
        self.position = position if position is not None else Point()
        self.orientation = orientation if orientation is not None else Quaternion()

    def __str__(self):
        """
        String representation of the Pose object.
        """
        return f"Position: {self.position}\nOrientation: {self.orientation}"
