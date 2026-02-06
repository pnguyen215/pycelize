"""
Participant Name Generator

This module provides utilities for generating unique, memorable participant names
using themes like sea animals, land animals, and celestial objects.
"""

import random
from typing import List


class NameGenerator:
    """
    Generates unique participant names using various naming themes.

    The generator combines themed names with random numbers to create
    unique, memorable identifiers for chat participants.
    """

    # Sea animals
    SEA_ANIMALS = [
        "BlueWhale", "Dolphin", "Seahorse", "Octopus", "Jellyfish",
        "Starfish", "SeaTurtle", "Shark", "Manta", "Orca",
        "Penguin", "Seal", "Walrus", "Crab", "Lobster",
        "Clownfish", "Barracuda", "Swordfish", "Marlin", "Tuna"
    ]

    # Land animals
    LAND_ANIMALS = [
        "Tiger", "Lion", "Elephant", "Giraffe", "Zebra",
        "Panda", "Koala", "Kangaroo", "Fox", "Wolf",
        "Bear", "Deer", "Rabbit", "Squirrel", "Otter",
        "Lynx", "Cheetah", "Leopard", "Jaguar", "Panther"
    ]

    # Celestial objects (asteroids and stars)
    CELESTIAL_OBJECTS = [
        "Orion", "Andromeda", "Sirius", "Vega", "Polaris",
        "Cassiopeia", "Pegasus", "Draco", "Phoenix", "Cygnus",
        "Ceres", "Vesta", "Pallas", "Juno", "Iris",
        "Flora", "Metis", "Hygeia", "Parthenos", "Victoria"
    ]

    @staticmethod
    def generate(theme: str = "random") -> str:
        """
        Generate a unique participant name.

        Args:
            theme: Naming theme - 'sea', 'land', 'celestial', or 'random'

        Returns:
            Generated name in format: "ThemeName-####"

        Example:
            >>> NameGenerator.generate('sea')
            'BlueWhale-4821'
            >>> NameGenerator.generate('celestial')
            'OrionAsteroid-9923'
        """
        if theme == "sea":
            name_list = NameGenerator.SEA_ANIMALS
        elif theme == "land":
            name_list = NameGenerator.LAND_ANIMALS
        elif theme == "celestial":
            name_list = NameGenerator.CELESTIAL_OBJECTS
        else:
            # Random theme
            all_names = (
                NameGenerator.SEA_ANIMALS
                + NameGenerator.LAND_ANIMALS
                + NameGenerator.CELESTIAL_OBJECTS
            )
            name_list = all_names

        name = random.choice(name_list)
        number = random.randint(1000, 9999)

        return f"{name}-{number}"

    @staticmethod
    def generate_batch(count: int, theme: str = "random") -> List[str]:
        """
        Generate multiple unique participant names.

        Args:
            count: Number of names to generate
            theme: Naming theme - 'sea', 'land', 'celestial', or 'random'

        Returns:
            List of generated names

        Example:
            >>> names = NameGenerator.generate_batch(3, 'sea')
            >>> len(names)
            3
        """
        return [NameGenerator.generate(theme) for _ in range(count)]
