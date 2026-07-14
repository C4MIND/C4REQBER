"""
TRIZ 40 Inventive Principles with full descriptions, examples, and sub-principles.
Based on the classical TRIZ methodology developed by Genrich Altshuller.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SubPrinciple:
    """A sub-principle or specific technique within a principle."""
    name: str
    description: str
    examples: list[str]


@dataclass(frozen=True)
class Principle:
    """One of the 40 Inventive Principles of TRIZ."""
    number: int
    name: str
    description: str
    examples: list[str]
    sub_principles: list[SubPrinciple]


# =============================================================================
# 40 INVENTIVE PRINCIPLES
# =============================================================================

PRINCIPLES: dict[int, Principle] = {
    1: Principle(
        number=1,
        name="Segmentation",
        description="Divide an object into independent parts; make an object sectional; increase the degree of an object's segmentation.",
        examples=[
            "Modular furniture that can be rearranged",
            "Sectional sofa with detachable pieces",
            "Computer hard drive partitioned into segments",
            "Segmented windshield wipers for better contact",
        ],
        sub_principles=[
            SubPrinciple(
                name="Divide into parts",
                description="Separate an object into independent parts.",
                examples=["Personal computers instead of mainframes", "Modular kitchen cabinets"],
            ),
            SubPrinciple(
                name="Make sectional",
                description="Make an object easy to disassemble.",
                examples=["Quick-release bicycle wheels", "Snap-together toys"],
            ),
            SubPrinciple(
                name="Increase segmentation",
                description="Increase the degree of fragmentation.",
                examples=["Powdered instant coffee", "Granular fertilizer", "Pixel-based displays"],
            ),
        ],
    ),
    2: Principle(
        number=2,
        name="Taking Out / Extraction",
        description="Separate an interfering part or property from an object, or single out the only necessary part (or property) of an object.",
        examples=[
            "Noise-canceling headphones extract and cancel ambient noise",
            "Extracting pure metals from ore",
            "Removing seeds from grapes for seedless varieties",
            "Isolating active pharmaceutical ingredients",
        ],
        sub_principles=[
            SubPrinciple(
                name="Remove interfering part",
                description="Separate the disturbing part from the object.",
                examples=["Removing a rotten apple from a barrel", "Filtering impurities from water"],
            ),
            SubPrinciple(
                name="Extract only necessary part",
                description="Isolate only the essential component.",
                examples=["Concentrated juice", "Essential oils from plants", "Protein isolates"],
            ),
        ],
    ),
    3: Principle(
        number=3,
        name="Local Quality",
        description="Change an object's structure from uniform to non-uniform; let each part of an object function in conditions most suitable for its operation; make each part of an object fulfill a different and useful function.",
        examples=[
            "Multi-tool Swiss Army knife",
            "Ergonomic keyboard with different key shapes",
            "Fishing rod with flexible tip and rigid base",
            "Camera lens with varying refractive index",
        ],
        sub_principles=[
            SubPrinciple(
                name="Transition from uniform to non-uniform",
                description="Change the structure to vary properties across the object.",
                examples=["Gradient-index lenses", "Functionally graded materials"],
            ),
            SubPrinciple(
                name="Optimal conditions for each part",
                description="Each part operates in its most suitable environment.",
                examples=["Work gloves with reinforced palms and breathable backs", "Winter jacket with waterproof shell and insulated lining"],
            ),
            SubPrinciple(
                name="Different functions for each part",
                description="Each component serves a distinct purpose.",
                examples=["Pen with built-in stylus", "Phone case with integrated wallet"],
            ),
        ],
    ),
    4: Principle(
        number=4,
        name="Asymmetry",
        description="Change the shape of an object from symmetrical to asymmetrical; if an object is asymmetrical, increase its degree of asymmetry.",
        examples=[
            "Asymmetric tire tread for better water evacuation",
            "Ergonomic mouse shaped for right hand",
            "Asymmetric wing designs for aircraft stability",
            "Off-center loading in washing machines for better tumbling",
        ],
        sub_principles=[
            SubPrinciple(
                name="Replace symmetrical with asymmetrical",
                description="Change from symmetric to asymmetric form.",
                examples=["Human heart located off-center", "Car headlights with asymmetric beam pattern"],
            ),
            SubPrinciple(
                name="Increase asymmetry",
                description="If already asymmetric, increase the degree.",
                examples=["Dihedral aircraft wings", "Tapered beams for structural efficiency"],
            ),
        ],
    ),
    5: Principle(
        number=5,
        name="Merging / Consolidation",
        description="Bring closer together (or merge) identical or similar objects, assemble identical or similar parts to perform parallel operations; make operations contiguous or parallel.",
        examples=[
            "Personal digital assistant (PDA) merging phone, calendar, contacts",
            "Multi-core processors performing parallel computations",
            "Combined washer-dryer unit",
            "USB hub merging multiple ports",
        ],
        sub_principles=[
            SubPrinciple(
                name="Merge identical objects",
                description="Bring similar objects or operations together.",
                examples=["Tandem bicycle", "Dual-monitor setup", "Multi-blade razors"],
            ),
            SubPrinciple(
                name="Parallel operations",
                description="Perform operations simultaneously rather than sequentially.",
                examples=["SIMD processor instructions", "Assembly line with parallel stations"],
            ),
            SubPrinciple(
                name="Contiguous operations",
                description="Make sequential operations adjacent in time or space.",
                examples=["Drive-through banking", "Print-on-demand publishing"],
            ),
        ],
    ),
    6: Principle(
        number=6,
        name="Universality",
        description="Make a part or object perform multiple functions; eliminate the need for other parts.",
        examples=[
            "Smartphone as camera, GPS, music player, and communication device",
            "Sofa bed serving as both seating and sleeping furniture",
            "Multifunction printer (print, scan, copy, fax)",
            "Adjustable wrench fitting multiple nut sizes",
        ],
        sub_principles=[
            SubPrinciple(
                name="Multi-function parts",
                description="One component serves multiple purposes.",
                examples=["Car seat that folds into cargo space", "Window that also serves as emergency exit"],
            ),
            SubPrinciple(
                name="Eliminate redundant parts",
                description="Remove parts whose functions are covered by others.",
                examples=["Touchscreen replacing physical keyboard and mouse", "LED indicators integrated into buttons"],
            ),
        ],
    ),
    7: Principle(
        number=7,
        name="Nested Doll / Matryoshka",
        description="Place one object inside another; place each object, in turn, inside the other; make one part pass through a cavity in the other.",
        examples=[
            "Telescoping antenna",
            "Russian nesting dolls",
            "Retractable ballpoint pen",
            "Nested measuring cups",
            "Extendable selfie stick",
        ],
        sub_principles=[
            SubPrinciple(
                name="Object inside another",
                description="One object is contained within another.",
                examples=["Ink cartridge inside pen", "USB flash drive cap that stores on the drive"],
            ),
            SubPrinciple(
                name="Multiple nested objects",
                description="Several objects nested within each other.",
                examples=["Telescoping radio antenna", "Stacked traffic cones"],
            ),
            SubPrinciple(
                name="Part through cavity",
                description="One part moves through a hollow in another.",
                examples=["Sliding door in wall cavity", "Drawer slides through cabinet frame"],
            ),
        ],
    ),
    8: Principle(
        number=8,
        name="Anti-Weight / Weight Compensation",
        description="To compensate for the weight of an object, merge it with other objects that provide lift; to compensate for the weight of an object, make it interact with the environment (e.g., aerodynamic, hydrodynamic, buoyancy, and other forces).",
        examples=[
            "Hot air balloon using heated air for lift",
            "Hydrofoil boats using wing-like structures for lift",
            "Maglev trains using magnetic levitation",
            "Swim bladder in fish for buoyancy control",
        ],
        sub_principles=[
            SubPrinciple(
                name="Merge with lifting objects",
                description="Combine with objects or media that provide upward force.",
                examples=["Helium balloons lifting weather instruments", "Foam inserts in life jackets"],
            ),
            SubPrinciple(
                name="Environmental interaction",
                description="Use aerodynamic, hydrodynamic, or other environmental forces.",
                examples=["Airplane wings generating lift", "Kite surfing using wind force", "Submarine ballast tanks"],
            ),
        ],
    ),
    9: Principle(
        number=9,
        name="Preliminary Anti-Action",
        description="If it will be necessary to do an action with both harmful and useful effects, this action should be replaced with anti-actions to control harmful effects; create beforehand stresses in an object that will oppose known undesirable working stresses later.",
        examples=[
            "Pre-stressed concrete with compression to counteract tension loads",
            "Vaccination creating immunity before disease exposure",
            "Pre-heating an engine before cold start",
            "Anti-lock braking system (ABS) preventing wheel lock",
        ],
        sub_principles=[
            SubPrinciple(
                name="Pre-apply opposite action",
                description="Apply the reverse action in advance to neutralize harmful effects.",
                examples=["Tempered glass with surface compression", "Pre-tensioned bridge cables"],
            ),
            SubPrinciple(
                name="Pre-stress against known loads",
                description="Create internal stresses that oppose expected external stresses.",
                examples=["Pre-loaded springs", "Reinforced concrete with rebar in tension zones"],
            ),
        ],
    ),
    10: Principle(
        number=10,
        name="Preliminary Action",
        description="Perform, before it is needed, the required change of an object (either fully or partially); pre-arrange objects such that they can come into action from the most convenient place and without losing time for their delivery.",
        examples=[
            "Pre-printed forms with common fields already filled",
            "Pre-filled syringes for emergency medicine",
            "Just-in-time manufacturing with pre-staged parts",
            "Pre-loaded software on new computers",
        ],
        sub_principles=[
            SubPrinciple(
                name="Complete action in advance",
                description="Perform the full required change beforehand.",
                examples=["Pre-fabricated building components", "Pre-cooked meals"],
            ),
            SubPrinciple(
                name="Partial action in advance",
                description="Perform part of the required change beforehand.",
                examples=["Pre-drilled holes for assembly", "Pre-mixed dry ingredients for baking"],
            ),
            SubPrinciple(
                name="Pre-position for convenience",
                description="Place objects where they'll be needed.",
                examples=["Tool cribs near workstations", "Emergency exits clearly marked and accessible"],
            ),
        ],
    ),
    11: Principle(
        number=11,
        name="Beforehand Cushioning / Cushion in Advance",
        description="Prepare emergency means beforehand to compensate for the relatively low reliability of an object.",
        examples=[
            "Spare tire in automobiles",
            "Backup power generators for hospitals",
            "Parachute as emergency landing system",
            "Redundant data backups",
            "Emergency air masks on airplanes",
        ],
        sub_principles=[
            SubPrinciple(
                name="Emergency backup systems",
                description="Have standby systems ready for critical failures.",
                examples=["UPS battery backup for computers", "Reserve fuel tanks in aircraft"],
            ),
            SubPrinciple(
                name="Compensate for low reliability",
                description="Add redundancy where reliability is insufficient.",
                examples=["RAID disk arrays", "Dual-control systems in aircraft", "Emergency brakes"],
            ),
        ],
    ),
    12: Principle(
        number=12,
        name="Equipotentiality",
        description="In a potential field, limit position changes (e.g., change operating conditions to eliminate the need to raise or lower objects in a gravity field).",
        examples=[
            "Spring-loaded shelves that rise to counter height when unloaded",
            "Hydraulic car lifts that bring work to mechanic height",
            "Assembly line at constant height",
            "Spring-loaded tape dispensers keeping tape at constant level",
        ],
        sub_principles=[
            SubPrinciple(
                name="Eliminate height changes",
                description="Change conditions so objects don't need to be lifted or lowered.",
                examples=["Spring-loaded pallet positioners", "Adjustable-height desks"],
            ),
            SubPrinciple(
                name="Work in potential field equilibrium",
                description="Operate at positions where potential energy is balanced.",
                examples=["Counterbalanced windows", "Neutral buoyancy in submarines"],
            ),
        ],
    ),
    13: Principle(
        number=13,
        name="The Other Way Round / Inversion",
        description="Invert the action(s) used to solve the problem; make movable parts (or the external environment) fixed and fixed parts movable; turn the object (or process) 'upside down'.",
        examples=[
            "Rotating the part instead of the tool (lathe)",
            "Treadmill (moving floor instead of moving person)",
            "Upside-down ketchup bottle",
            "Inverted microscope (objective below specimen)",
            "Escalator (moving stairs instead of moving person)",
        ],
        sub_principles=[
            SubPrinciple(
                name="Invert the action",
                description="Do the opposite of the usual approach.",
                examples=["Cooling from inside instead of outside", "Heating from outside in instead of inside out"],
            ),
            SubPrinciple(
                name="Make fixed parts movable",
                description="Swap which parts move and which are stationary.",
                examples=["Rotary table in machining", "Moving sidewalk at airports"],
            ),
            SubPrinciple(
                name="Turn object upside down",
                description="Physically or conceptually invert the object.",
                examples=["Pouring from bottom of container", "Upside-down cake baking"],
            ),
        ],
    ),
    14: Principle(
        number=14,
        name="Spheroidality - Curvature",
        description="Instead of using rectilinear parts, surfaces, or forms, use curvilinear ones; move from flat surfaces to spherical ones; from parts shaped as cubes or parallelepipeds to spherical structures; use rollers, balls, spirals, domes; go from linear to rotary motion, use centrifugal forces.",
        examples=[
            "Ball bearings replacing sliding friction",
            "Domed stadium roofs for strength",
            "Spiral staircase saving space",
            "Curved windshields for aerodynamics",
            "Centrifugal pumps for fluid movement",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use curved instead of flat",
                description="Replace rectilinear elements with curvilinear ones.",
                examples=["Curved smartphone screens", "Arched bridges", "Parabolic reflectors"],
            ),
            SubPrinciple(
                name="Use rollers and balls",
                description="Introduce rolling elements to reduce friction.",
                examples=["Ball bearings", "Roller conveyors", "Caster wheels"],
            ),
            SubPrinciple(
                name="Linear to rotary motion",
                description="Convert motion types to use centrifugal forces.",
                examples=["Centrifugal clutches", "Spin dryers", "Cyclone separators"],
            ),
        ],
    ),
    15: Principle(
        number=15,
        name="Dynamics",
        description="Allow (or design) the characteristics of an object, external environment, or process to change to be optimal or to find an optimal operating condition; divide an object into parts capable of movement relative to each other; if an object (or process) is rigid or inflexible, make it movable or adaptive.",
        examples=[
            "Adjustable office chair with multiple degrees of freedom",
            "Adaptive cruise control adjusting speed to traffic",
            "Flexible manufacturing systems",
            "Shape-memory alloys",
            "Transformable furniture",
        ],
        sub_principles=[
            SubPrinciple(
                name="Allow characteristics to change",
                description="Design objects with adjustable properties.",
                examples=["Variable-pitch propellers", "Adjustable suspension systems", "Dimmer switches"],
            ),
            SubPrinciple(
                name="Divide into relatively moving parts",
                description="Create objects with multiple moving components.",
                examples=["Articulated robot arms", "Folding bicycles", "Modular robots"],
            ),
            SubPrinciple(
                name="Make rigid objects movable",
                description="Introduce flexibility where there was rigidity.",
                examples=["Flexible printed circuit boards", "Hinged containers", "Collapsible drinking cups"],
            ),
        ],
    ),
    16: Principle(
        number=16,
        name="Partial or Excessive Actions",
        description="If exactly the desired effect is difficult to achieve, slightly increase or decrease the action to make it easier; use a little more or a little less than the exact amount needed.",
        examples=[
            "Overfilling a mold and then machining to exact dimensions",
            "Applying slightly more paint than needed and wiping excess",
            "Overshooting a target and correcting back",
            "Pre-loading with excess and trimming to fit",
        ],
        sub_principles=[
            SubPrinciple(
                name="Slightly more than needed",
                description="Apply excess and then remove the surplus.",
                examples=["Pouring concrete and leveling", "Printing oversized and trimming", "Casting with machining allowance"],
            ),
            SubPrinciple(
                name="Slightly less than needed",
                description="Apply less and then add more if needed.",
                examples=["Adding seasoning gradually", "Underexposing photo and adjusting in post"],
            ),
        ],
    ),
    17: Principle(
        number=17,
        name="Another Dimension",
        description="Move an object in two- or three-dimensional space; use a multi-story arrangement of objects instead of a single-story arrangement; tilt or re-orient the object, lay it on its side; use 'another side' of a given area.",
        examples=[
            "Multi-story parking garages",
            "Double-sided printed circuit boards",
            "Stacked memory chips in 3D packaging",
            "Overhead storage in airplanes",
            "Vertical farming in urban environments",
        ],
        sub_principles=[
            SubPrinciple(
                name="Move to 2D or 3D space",
                description="Use additional spatial dimensions.",
                examples=["3D printing instead of 2D machining", "Multi-level road interchanges"],
            ),
            SubPrinciple(
                name="Multi-story arrangement",
                description="Stack objects vertically instead of spreading horizontally.",
                examples=["High-rise buildings", "Multi-tiered server racks", "Stacked washer-dryer units"],
            ),
            SubPrinciple(
                name="Tilt or re-orient",
                description="Change the orientation of the object or process.",
                examples=["Tilted computer monitors", "Angled solar panels", "Sideways-mounted engines"],
            ),
        ],
    ),
    18: Principle(
        number=18,
        name="Mechanical Vibration",
        description="Cause an object to oscillate or vibrate; increase its frequency (even up to the ultrasonic); use an object's resonant frequency; use piezoelectric vibrators instead of mechanical ones; use combined ultrasonic and electromagnetic field oscillations.",
        examples=[
            "Vibrating concrete to remove air bubbles",
            "Ultrasonic cleaning of jewelry",
            "Vibrating feeder bowls for part orientation",
            "Quartz crystal oscillators in watches",
            "Vibrating alert in mobile phones",
        ],
        sub_principles=[
            SubPrinciple(
                name="Cause to vibrate",
                description="Introduce oscillation to the object or process.",
                examples=["Vibrating sieves for sorting", "Oscillating sprinklers", "Vibration plates for fitness"],
            ),
            SubPrinciple(
                name="Increase frequency",
                description="Raise the vibration frequency, potentially to ultrasonic levels.",
                examples=["Ultrasonic welding", "High-frequency dental tools", "Ultrasonic humidifiers"],
            ),
            SubPrinciple(
                name="Use resonant frequency",
                description="Match the frequency to the object's natural resonance.",
                examples=["Resonant frequency destruction of kidney stones", "Tuning fork resonance", "Musical instrument design"],
            ),
            SubPrinciple(
                name="Piezoelectric vibrators",
                description="Use piezoelectric effect for precise vibration control.",
                examples=["Inkjet printer nozzles", "Atomic force microscopy", "Medical ultrasound transducers"],
            ),
        ],
    ),
    19: Principle(
        number=19,
        name="Periodic Action",
        description="Instead of continuous action, use periodic or pulsating actions; if an action is already periodic, change the periodic magnitude or frequency; use pauses between impulses to perform a different action.",
        examples=[
            "Intermittent windshield wipers",
            "Pulsating sprinkler systems",
            "PWM (Pulse Width Modulation) for motor control",
            "Strobe lights for motion analysis",
            "Intermittent fasting for health",
        ],
        sub_principles=[
            SubPrinciple(
                name="Replace continuous with periodic",
                description="Change steady action to intermittent action.",
                examples=["Pulsed laser instead of continuous beam", "Blinking turn signals", "Pulse dialing"],
            ),
            SubPrinciple(
                name="Change periodic parameters",
                description="Adjust frequency, amplitude, or duty cycle.",
                examples=["Variable intermittent wipers", "Adjustable PWM frequency", "Variable strobe rate"],
            ),
            SubPrinciple(
                name="Use pauses productively",
                description="Utilize the intervals between actions for other purposes.",
                examples=["Time-division multiplexing", "Breathing between speech phrases", "Cooling periods in welding"],
            ),
        ],
    ),
    20: Principle(
        number=20,
        name="Continuity of Useful Action",
        description="Carry on work continuously; make all parts of an object work at full load, all the time; eliminate all idle or intermittent actions or work.",
        examples=[
            "Flywheel storing energy for continuous output",
            "Continuous casting in steel production",
            "Printer that can print while receiving data",
            "Continuously variable transmission (CVT)",
            "Assembly line with no downtime between products",
        ],
        sub_principles=[
            SubPrinciple(
                name="Work continuously",
                description="Eliminate interruptions in the work process.",
                examples=["24/7 manufacturing", "Continuous flow chemistry", "Always-on internet connection"],
            ),
            SubPrinciple(
                name="Full load all the time",
                description="Ensure all components are utilized at maximum capacity.",
                examples=["Multi-threaded processors", "Pipeline processing in CPUs", "Load-balanced servers"],
            ),
            SubPrinciple(
                name="Eliminate idle time",
                description="Remove waiting periods and downtime.",
                examples=["Just-in-time manufacturing", "Overlapping production shifts", "Prefetching data in CPUs"],
            ),
        ],
    ),
    21: Principle(
        number=21,
        name="Skipping / Rushing Through",
        description="Conduct a process, or certain stages (e.g., destructive, harmful, or hazardous operations) at high speed.",
        examples=[
            "High-speed photography capturing fast events",
            "Rapid cutting to reduce heat buildup",
            "Quick-freezing to preserve cell structure",
            "High-speed injection molding",
            "Flash welding minimizing heat-affected zone",
        ],
        sub_principles=[
            SubPrinciple(
                name="High-speed harmful operations",
                description="Complete damaging processes quickly to minimize harm.",
                examples=["Rapid amputation in surgery", "Quick ripping of adhesive bandages", "Fast chemical etching"],
            ),
            SubPrinciple(
                name="Rush through critical stages",
                description="Accelerate through phases where problems accumulate.",
                examples=["High-speed pass through danger zone", "Rapid cooling to prevent crystallization"],
            ),
        ],
    ),
    22: Principle(
        number=22,
        name="Blessing in Disguise / Turn Lemons into Lemonade",
        description="Use harmful factors (particularly, harmful effects of the environment or surroundings) to achieve a positive effect; eliminate the primary harmful action by adding it to another harmful action to resolve the problem; amplify the harmful factor to such a degree that it ceases to be harmful.",
        examples=[
            "Using waste heat from industrial processes for heating",
            "Recycling CO2 into fuel or chemicals",
            "Using noise-canceling to create silence",
            "Controlled burns to prevent larger wildfires",
            "Using vibrations to compact materials",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use harmful factors positively",
                description="Turn negative effects into beneficial ones.",
                examples=["Waste heat recovery systems", "Using pests as biological control", "Floodwater for irrigation"],
            ),
            SubPrinciple(
                name="Combine harmful actions",
                description="Add harmful effects together to neutralize or resolve them.",
                examples=["Chemical neutralization reactions", "Counter-rotating vibrations canceling each other"],
            ),
            SubPrinciple(
                name="Amplify to harmlessness",
                description="Increase the harmful factor until its nature changes.",
                examples=["Over-saturating a market to drive out competitors", "Controlled burning of fuel to prevent explosion"],
            ),
        ],
    ),
    23: Principle(
        number=23,
        name="Feedback",
        description="Introduce feedback (referring back, cross-checking) to improve a process or action; if feedback is already used, change its magnitude or influence.",
        examples=[
            "Thermostat controlling room temperature",
            "Cruise control maintaining vehicle speed",
            "Noise-canceling headphones with adaptive feedback",
            "Statistical process control in manufacturing",
            "Biofeedback for stress management",
        ],
        sub_principles=[
            SubPrinciple(
                name="Introduce feedback",
                description="Add a feedback loop to monitor and adjust the process.",
                examples=["Closed-loop motor control", "Customer satisfaction surveys", "Quality control checkpoints"],
            ),
            SubPrinciple(
                name="Change feedback parameters",
                description="Modify the feedback gain, delay, or type.",
                examples=["PID controller tuning", "Adaptive algorithms", "Predictive feedback"],
            ),
            SubPrinciple(
                name="Eliminate feedback if harmful",
                description="Remove feedback when it causes oscillation or instability.",
                examples=["Open-loop control for simplicity", "Feedforward control instead of feedback"],
            ),
        ],
    ),
    24: Principle(
        number=24,
        name="Intermediary / Mediator",
        description="Use an intermediary carrier article or intermediary process; merge one object temporarily with another (which can be easily removed).",
        examples=[
            "Catalyst in chemical reactions",
            "Solder as intermediary for joining metals",
            "Glue as intermediary bonding agent",
            "Handle on a tool as intermediary between hand and workpiece",
            "Pallet as intermediary for moving goods",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use intermediary object",
                description="Insert a third object between two interacting objects.",
                examples=["Gloves between hand and hot object", "Buffer solution in chemistry", "Adapter between incompatible interfaces"],
            ),
            SubPrinciple(
                name="Use intermediary process",
                description="Add a step between two operations.",
                examples=["Pre-treatment before painting", "Annealing between forming operations", "Proofreading before publishing"],
            ),
            SubPrinciple(
                name="Temporary merge",
                description="Combine objects temporarily for a process, then separate.",
                examples=["Temporary adhesives", "Removable templates for drilling", "Sacrificial layers in manufacturing"],
            ),
        ],
    ),
    25: Principle(
        number=25,
        name="Self-Service",
        description="Make an object serve itself by performing auxiliary helpful functions; use waste resources, energy, or substances.",
        examples=[
            "Self-sharpening lawn mower blades",
            "Self-lubricating bearings",
            "Self-cleaning ovens using pyrolysis",
            "Regenerative braking in electric vehicles",
            "Self-winding mechanical watches",
        ],
        sub_principles=[
            SubPrinciple(
                name="Self-performing auxiliary functions",
                description="The object performs maintenance on itself.",
                examples=["Self-cleaning camera lenses", "Self-aligning bearings", "Self-tuning guitars"],
            ),
            SubPrinciple(
                name="Use waste resources",
                description="Recapture and reuse waste energy or materials.",
                examples=["Waste heat recovery", "Composting organic waste", "Rainwater harvesting"],
            ),
        ],
    ),
    26: Principle(
        number=26,
        name="Copying",
        description="Instead of an unavailable, expensive, fragile object, use simpler and inexpensive copies; replace an object or process with optical copies; if visible optical copies are used, replace them with infrared or ultraviolet copies.",
        examples=[
            "Virtual reality training simulators",
            "Medical imaging instead of exploratory surgery",
            "Wind tunnel testing with scale models",
            "Digital twins for factory optimization",
            "Photocopies instead of original documents",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use simplified copies",
                description="Substitute with inexpensive replicas.",
                examples=["Crash test dummies", "Architectural scale models", "Flight simulators"],
            ),
            SubPrinciple(
                name="Optical copies",
                description="Use image-based representations.",
                examples=["X-rays instead of surgery", "Satellite imagery instead of ground surveys", "Video conferencing instead of travel"],
            ),
            SubPrinciple(
                name="Invisible copies",
                description="Use infrared, ultraviolet, or other non-visible representations.",
                examples=["Thermal imaging", "UV fluorescence inspection", "X-ray crystallography"],
            ),
        ],
    ),
    27: Principle(
        number=27,
        name="Cheap Short-Living Objects",
        description="Replace an expensive object with a multiple of inexpensive objects, comprising certain qualities (such as service life, for instance).",
        examples=[
            "Disposable razors instead of straight razors",
            "Paper cups instead of ceramic mugs",
            "Single-use medical syringes",
            "Temporary phone numbers for verification",
            "Disposable cameras for events",
        ],
        sub_principles=[
            SubPrinciple(
                name="Replace expensive with multiple cheap",
                description="Use many low-cost items instead of one costly item.",
                examples=["Disposable pipettes in labs", "Paper plates for picnics", "Temporary workers for seasonal demand"],
            ),
            SubPrinciple(
                name="Accept reduced service life",
                description="Trade durability for cost savings when appropriate.",
                examples=["Biodegradable packaging", "Single-use medical gowns", "Temporary event signage"],
            ),
        ],
    ),
    28: Principle(
        number=28,
        name="Mechanics Substitution",
        description="Replace a mechanical means with a sensory (optical, acoustic, taste or smell) means; use electric, magnetic, and electromagnetic fields to interact with the object; change from static to movable fields, from unstructured to structured fields; use fields in conjunction with field-activated particles.",
        examples=[
            "Electronic nose for smell detection",
            "Magnetic levitation instead of wheels",
            "Voice recognition instead of keyboard input",
            "Haptic feedback instead of mechanical buttons",
            "RFID tags instead of barcode scanning",
        ],
        sub_principles=[
            SubPrinciple(
                name="Sensory substitution",
                description="Replace mechanical interaction with sensory means.",
                examples=["Optical mice instead of ball mice", "Touchscreens instead of physical buttons", "Voice control instead of switches"],
            ),
            SubPrinciple(
                name="Field interaction",
                description="Use electromagnetic fields for interaction.",
                examples=["Wireless charging", "Magnetic resonance imaging (MRI)", "Induction cooking"],
            ),
            SubPrinciple(
                name="Structured and movable fields",
                description="Use fields with varying structure and mobility.",
                examples=["Phased array radar", "Variable magnetic field motors", "Structured light 3D scanning"],
            ),
        ],
    ),
    29: Principle(
        number=29,
        name="Pneumatics and Hydraulics",
        description="Use gas and liquid parts of an object instead of solid parts (e.g., inflatable, filled with liquids, air cushion, hydrostatic, hydro-reactive); use air or water for cushioning, support, or transmission.",
        examples=[
            "Air cushion vehicles (hovercraft)",
            "Hydraulic brakes in automobiles",
            "Pneumatic actuators in automation",
            "Inflatable structures for temporary buildings",
            "Hydrostatic bearings for precision machinery",
        ],
        sub_principles=[
            SubPrinciple(
                name="Replace solids with gases",
                description="Use air or gas for structural or functional elements.",
                examples=["Air springs in vehicles", "Pneumatic tires", "Inflatable splints", "Air bearings"],
            ),
            SubPrinciple(
                name="Replace solids with liquids",
                description="Use water or other liquids for support or transmission.",
                examples=["Hydraulic lifts", "Water beds", "Liquid-cooled engines", "Hydraulic presses"],
            ),
            SubPrinciple(
                name="Cushioning and support",
                description="Use fluids for shock absorption and support.",
                examples=["Shock absorbers with hydraulic fluid", "Airbags in cars", "Pneumatic damping systems"],
            ),
        ],
    ),
    30: Principle(
        number=30,
        name="Flexible Shells and Thin Films",
        description="Use flexible shells and thin films instead of three-dimensional structures; isolate the object from the external environment using flexible shells and thin films.",
        examples=[
            "Plastic wrap for food preservation",
            "Membrane filters for water purification",
            "Inflatable kayak made of durable film",
            "Thin-film solar cells",
            "Condoms as barrier protection",
        ],
        sub_principles=[
            SubPrinciple(
                name="Replace 3D with thin films",
                description="Use thin layers instead of bulk materials.",
                examples=["Thin-film transistors", "Coatings instead of solid plates", "Laminate flooring"],
            ),
            SubPrinciple(
                name="Isolate with films",
                description="Use membranes or films as barriers.",
                examples=["Gore-Tex waterproof fabric", "Oxygen barrier packaging", "Protective screen protectors"],
            ),
            SubPrinciple(
                name="Flexible shells",
                description="Use deformable thin-walled structures.",
                examples=["Bubble wrap", "Blister packaging", "Inflatable air beams"],
            ),
        ],
    ),
    31: Principle(
        number=31,
        name="Porous Materials",
        description="Make an object porous or add porous elements (inserts, coatings, etc.); if an object is already porous, use the pores to introduce a useful substance or function.",
        examples=[
            "Porous concrete for drainage",
            "Activated carbon filters for air purification",
            "Foam padding for cushioning",
            "Porous ceramics for bone implants",
            "Breathable waterproof fabrics with micropores",
        ],
        sub_principles=[
            SubPrinciple(
                name="Make object porous",
                description="Introduce voids or pores into the material.",
                examples=["Aerogel insulation", "Foam rubber", "Sintered metal filters", "Porous asphalt"],
            ),
            SubPrinciple(
                name="Use pores functionally",
                description="Utilize the pore structure for a specific purpose.",
                examples=["Drug-eluting stents", "Scent-infused plastics", "Self-lubricating porous bearings"],
            ),
        ],
    ),
    32: Principle(
        number=32,
        name="Color Changes",
        description="Change the color of an object or its external environment; change the transparency of an object or its external environment; use color additives to observe objects or processes that are difficult to see; if such additives are already used, employ luminescent traces or trace atoms.",
        examples=[
            "Thermochromic materials indicating temperature",
            "Photochromic lenses that darken in sunlight",
            "Fluorescent dyes in biological research",
            "Color-changing paint indicating wear",
            "Transparent cookware for visual monitoring",
        ],
        sub_principles=[
            SubPrinciple(
                name="Change object color",
                description="Alter the color of the object itself.",
                examples=["Camouflage patterns", "Anodized aluminum", "Color-coded wiring"],
            ),
            SubPrinciple(
                name="Change environment color",
                description="Alter the surroundings to improve visibility or contrast.",
                examples=["Green surgical scrubs reducing eye strain", "White balance in photography", "Anti-glare screens"],
            ),
            SubPrinciple(
                name="Change transparency",
                description="Make objects transparent or opaque as needed.",
                examples=["Smart glass windows", "Transparent OLED displays", "Privacy film on windows"],
            ),
            SubPrinciple(
                name="Use additives and tracers",
                description="Add substances to make invisible things visible.",
                examples=["Fluorescent leak detection dye", "Radioactive tracers in medicine", "UV security ink"],
            ),
        ],
    ),
    33: Principle(
        number=33,
        name="Homogeneity",
        description="Make objects interact with a given object of the same material (or material with identical properties).",
        examples=[
            "Friction welding of identical plastics",
            "Self-healing materials using same-material fillers",
            "Diamond cutting with diamond dust",
            "Ice cubes made from the same water as the drink",
            "Welding same metals together",
        ],
        sub_principles=[
            SubPrinciple(
                name="Same material interaction",
                description="Objects that interact should be of the same material.",
                examples=["Ceramic-on-ceramic hip replacements", "Same-metal contacts reducing galvanic corrosion", "Paper labels on paper packaging"],
            ),
        ],
    ),
    34: Principle(
        number=34,
        name="Discarding and Recovering",
        description="Make portions of an object that have fulfilled their functions go away (discard by dissolving, evaporating, etc.) or modify these directly during operation; conversely, restore consumable parts of an object directly in operation.",
        examples=[
            "Biodegradable packaging that dissolves",
            "Rocket stages that separate and fall away",
            "Dissolvable stitches in surgery",
            "Self-sharpening pencils",
            "Ice cube molds that peel away",
        ],
        sub_principles=[
            SubPrinciple(
                name="Discard after use",
                description="Remove parts that have served their purpose.",
                examples=["Booster rocket separation", "Peel-off masks", "Release agents in casting", "Burnable fuses"],
            ),
            SubPrinciple(
                name="Dissolve or evaporate",
                description="Make parts disappear through chemical or physical means.",
                examples=["Sugar cubes in coffee", "Sublimation cooling", "Water-soluble support in 3D printing"],
            ),
            SubPrinciple(
                name="Restore in operation",
                description="Replenish consumable parts during use.",
                examples=["Continuous ink supply systems", "Self-sharpening blades", "Regenerative catalysts"],
            ),
        ],
    ),
    35: Principle(
        number=35,
        name="Parameter Changes",
        description="Change an object's physical state (e.g., to a gas, liquid, or solid); change the concentration or consistency; change the degree of flexibility; change the temperature or volume.",
        examples=[
            "Liquid nitrogen for rapid freezing",
            "Thermoplastics that soften when heated",
            "Aerosol sprays converting liquid to fine mist",
            "Memory foam responding to body heat",
            "Freeze-drying for food preservation",
        ],
        sub_principles=[
            SubPrinciple(
                name="Change physical state",
                description="Transition between solid, liquid, and gas.",
                examples=["Steam cleaning", "Freeze-drying", "Vacuum forming of plastics", "Sublimation printing"],
            ),
            SubPrinciple(
                name="Change concentration",
                description="Adjust the density or consistency.",
                examples=["Concentrated cleaning products", "Thixotropic paints", "Diluted acids for etching"],
            ),
            SubPrinciple(
                name="Change flexibility",
                description="Alter the rigidity or elasticity.",
                examples=["Shape-memory alloys", "Thermoplastic elastomers", "Variable stiffness composites"],
            ),
            SubPrinciple(
                name="Change temperature",
                description="Use heating or cooling to change properties.",
                examples=["Hot-forming metals", "Cryogenic hardening", "Thermal expansion for fitting parts"],
            ),
        ],
    ),
    36: Principle(
        number=36,
        name="Phase Transitions",
        description="Use phenomena occurring during phase transitions (e.g., volume changes, loss or absorption of heat).",
        examples=[
            "Heat pipes using liquid-vapor phase change for cooling",
            "Refrigeration cycle using evaporation and condensation",
            "Steam engines using water-to-steam expansion",
            "Latent heat storage in phase change materials",
            "Freeze-thaw weathering in geology",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use volume changes",
                description="Exploit expansion or contraction during phase change.",
                examples=["Water expansion when freezing (ice breaking rocks)", "Thermal actuators", "Expanding foam insulation"],
            ),
            SubPrinciple(
                name="Use heat absorption/release",
                description="Utilize latent heat of phase transitions.",
                examples=["Evaporative cooling", "Condensation heating", "Phase change materials for temperature regulation"],
            ),
        ],
    ),
    37: Principle(
        number=37,
        name="Thermal Expansion",
        description="Use thermal expansion (or contraction) of materials; if thermal expansion is used, use multiple materials with different coefficients of thermal expansion.",
        examples=[
            "Bimetallic strips in thermostats",
            "Thermal fit: heating a part to expand it for assembly",
            "Expansion joints in bridges",
            "Liquid thermometers",
            "Shape-memory alloys activated by heat",
        ],
        sub_principles=[
            SubPrinciple(
                name="Use thermal expansion",
                description="Exploit natural expansion with temperature.",
                examples=["Thermal expansion valves in refrigeration", "Expansion tanks in heating systems", "Fire sprinklers with expanding liquid"],
            ),
            SubPrinciple(
                name="Multiple materials with different expansion",
                description="Combine materials that expand at different rates.",
                examples=["Bimetallic temperature sensors", "Thermostat switches", "Composite materials with controlled expansion"],
            ),
        ],
    ),
    38: Principle(
        number=38,
        name="Strong Oxidants",
        description="Replace common air with oxygen-enriched air; replace enriched air with pure oxygen; expose air or oxygen to ionizing radiation; use ionized oxygen; replace ozonized (or ionized) oxygen with ozone.",
        examples=[
            "Oxy-acetylene torch for cutting steel",
            "Hyperbaric oxygen therapy for wound healing",
            "Ozone water purification",
            "Oxygen-enriched combustion for efficiency",
            "Ionized air for static elimination",
        ],
        sub_principles=[
            SubPrinciple(
                name="Enriched air",
                description="Use air with higher oxygen content than normal.",
                examples=["Oxygen-enriched blast furnaces", "Medical oxygen therapy", "Scuba diving with nitrox"],
            ),
            SubPrinciple(
                name="Pure oxygen",
                description="Use 100% oxygen instead of air.",
                examples=["Liquid oxygen rocket engines", "Oxygen cutting torches", "Aquarium oxygenation systems"],
            ),
            SubPrinciple(
                name="Ionized or ozonized oxygen",
                description="Use chemically activated oxygen forms.",
                examples=["Ozone generators for water treatment", "Ionized air purifiers", "Corona discharge treatment of plastics"],
            ),
        ],
    ),
    39: Principle(
        number=39,
        name="Inert Atmosphere",
        description="Replace a normal environment with an inert one; add neutral parts, or inert additives to an object; carry out the process in a vacuum.",
        examples=[
            "Nitrogen flushing for food packaging",
            "Argon shielding in welding",
            "Vacuum deposition for thin films",
            "Inert gas fire suppression systems",
            "Vacuum insulation panels",
        ],
        sub_principles=[
            SubPrinciple(
                name="Inert environment",
                description="Replace reactive atmosphere with inert gas.",
                examples=["Helium atmosphere for semiconductor manufacturing", "Nitrogen blankets in chemical tanks", "Argon-filled windows"],
            ),
            SubPrinciple(
                name="Inert additives",
                description="Add neutral components to prevent unwanted reactions.",
                examples=["Anti-caking agents in powders", "Stabilizers in plastics", "Buffer salts in solutions"],
            ),
            SubPrinciple(
                name="Vacuum environment",
                description="Remove the atmosphere entirely.",
                examples=["Vacuum packaging", "Electron beam welding in vacuum", "Space simulation chambers", "Vacuum tubes"],
            ),
        ],
    ),
    40: Principle(
        number=40,
        name="Composite Materials",
        description="Change from uniform to composite (multiple) materials; change from homogeneous to heterogeneous materials.",
        examples=[
            "Carbon fiber reinforced polymers",
            "Reinforced concrete with steel rebar",
            "Fiberglass for boat hulls",
            "Particle board with wood chips and resin",
            "Functionally graded materials",
        ],
        sub_principles=[
            SubPrinciple(
                name="Combine multiple materials",
                description="Use composites to get the best properties of each component.",
                examples=["Kevlar-aramid composites", "Metal-matrix composites", "Ceramic-matrix composites"],
            ),
            SubPrinciple(
                name="Heterogeneous structure",
                description="Vary material composition across the object.",
                examples=["Sandwich panels with different core and face materials", "Gradient-index optical fibers", "Multi-layer circuit boards"],
            ),
        ],
    ),
}


def get_principle(number: int) -> Principle | None:
    """Get a principle by its number (1-40)."""
    return PRINCIPLES.get(number)


def get_all_principles() -> list[Principle]:
    """Get all 40 principles as a list."""
    return [PRINCIPLES[i] for i in range(1, 41)]


def search_principles(query: str) -> list[Principle]:
    """Search principles by name or description (case-insensitive)."""
    query_lower = query.lower()
    results = []
    for p in PRINCIPLES.values():
        if query_lower in p.name.lower() or query_lower in p.description.lower():
            results.append(p)
            continue
        for sp in p.sub_principles:
            if query_lower in sp.name.lower() or query_lower in sp.description.lower():
                results.append(p)
                break
    return results
