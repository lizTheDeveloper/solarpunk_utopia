// Resource categories and hierarchy for the gift economy

export interface ResourceCategory {
  id: string;
  name: string;
  subcategories: ResourceSubcategory[];
}

export interface ResourceSubcategory {
  id: string;
  name: string;
  items: string[];
}

export const RESOURCE_CATEGORIES: ResourceCategory[] = [
  {
    id: 'food',
    name: 'Food & Produce',
    subcategories: [
      {
        id: 'vegetables',
        name: 'Vegetables',
        items: ['Tomatoes', 'Lettuce', 'Carrots', 'Peppers', 'Onions', 'Garlic', 'Potatoes', 'Squash'],
      },
      {
        id: 'fruits',
        name: 'Fruits',
        items: ['Apples', 'Berries', 'Citrus', 'Stone Fruits', 'Melons', 'Grapes'],
      },
      {
        id: 'herbs',
        name: 'Herbs & Spices',
        items: ['Basil', 'Mint', 'Rosemary', 'Thyme', 'Cilantro', 'Parsley', 'Oregano'],
      },
      {
        id: 'preserves',
        name: 'Preserves & Canned Goods',
        items: ['Jams', 'Pickles', 'Sauces', 'Dried Goods'],
      },
    ],
  },
  {
    id: 'tools',
    name: 'Tools & Equipment',
    subcategories: [
      {
        id: 'garden_tools',
        name: 'Garden Tools',
        items: ['Shovels', 'Rakes', 'Hoes', 'Pruners', 'Watering Cans', 'Wheelbarrows'],
      },
      {
        id: 'hand_tools',
        name: 'Hand Tools',
        items: ['Hammers', 'Screwdrivers', 'Wrenches', 'Pliers', 'Saws'],
      },
      {
        id: 'power_tools',
        name: 'Power Tools',
        items: ['Drills', 'Sanders', 'Saws', 'Grinders'],
      },
    ],
  },
  {
    id: 'materials',
    name: 'Materials & Supplies',
    subcategories: [
      {
        id: 'building',
        name: 'Building Materials',
        items: ['Lumber', 'Bricks', 'Concrete', 'Insulation', 'Roofing', 'Hardware'],
      },
      {
        id: 'compost',
        name: 'Compost & Soil',
        items: ['Compost', 'Mulch', 'Potting Soil', 'Amendments', 'Fertilizer'],
      },
      {
        id: 'seeds',
        name: 'Seeds & Starts',
        items: ['Vegetable Seeds', 'Flower Seeds', 'Herb Seeds', 'Seedlings', 'Bulbs'],
      },
    ],
  },
  {
    id: 'skills',
    name: 'Skills & Services',
    subcategories: [
      {
        id: 'teaching',
        name: 'Teaching & Workshops',
        items: ['Gardening', 'Permaculture', 'Carpentry', 'Cooking', 'Crafts', 'Repair'],
      },
      {
        id: 'labor',
        name: 'Labor & Help',
        items: ['Garden Work', 'Construction', 'Moving', 'Childcare', 'Elder Care'],
      },
      {
        id: 'expertise',
        name: 'Expertise & Consulting',
        items: ['Design', 'Planning', 'Technical Support', 'Legal Advice'],
      },
    ],
  },
  {
    id: 'knowledge',
    name: 'Knowledge & Information',
    subcategories: [
      {
        id: 'guides',
        name: 'Guides & Manuals',
        items: ['Permaculture Guides', 'DIY Manuals', 'Repair Guides', 'Growing Guides'],
      },
      {
        id: 'protocols',
        name: 'Protocols & Standards',
        items: ['Network Protocols', 'Safety Protocols', 'Quality Standards'],
      },
      {
        id: 'education',
        name: 'Educational Materials',
        items: ['Videos', 'Books', 'Courses', 'Worksheets'],
      },
    ],
  },
  {
    id: 'energy',
    name: 'Energy & Power',
    subcategories: [
      {
        id: 'solar',
        name: 'Solar Equipment',
        items: ['Solar Panels', 'Charge Controllers', 'Batteries', 'Inverters'],
      },
      {
        id: 'wind',
        name: 'Wind Equipment',
        items: ['Wind Turbines', 'Controllers', 'Mounting Hardware'],
      },
      {
        id: 'storage',
        name: 'Energy Storage',
        items: ['Battery Banks', 'Capacitors', 'Flywheels'],
      },
    ],
  },
  {
    id: 'technology',
    name: 'Technology & Electronics',
    subcategories: [
      {
        id: 'computers',
        name: 'Computers & Devices',
        items: ['Laptops', 'Tablets', 'Phones', 'Raspberry Pi', 'Accessories'],
      },
      {
        id: 'networking',
        name: 'Networking Equipment',
        items: ['Routers', 'Access Points', 'Antennas', 'Cables', 'Switches'],
      },
      {
        id: 'sensors',
        name: 'Sensors & Monitoring',
        items: ['Temperature', 'Humidity', 'Soil Moisture', 'Air Quality', 'Water Quality'],
      },
    ],
  },
  {
    id: 'household',
    name: 'Household Goods',
    subcategories: [
      {
        id: 'furniture',
        name: 'Furniture',
        items: ['Tables', 'Chairs', 'Shelves', 'Beds', 'Storage'],
      },
      {
        id: 'kitchenware',
        name: 'Kitchenware',
        items: ['Pots', 'Pans', 'Dishes', 'Utensils', 'Appliances'],
      },
      {
        id: 'textiles',
        name: 'Textiles',
        items: ['Fabric', 'Yarn', 'Clothing', 'Bedding', 'Towels'],
      },
    ],
  },
];

// Helper functions
export const getCategoryById = (id: string): ResourceCategory | undefined => {
  return RESOURCE_CATEGORIES.find((cat) => cat.id === id);
};

export const getSubcategoryById = (
  categoryId: string,
  subcategoryId: string
): ResourceSubcategory | undefined => {
  const category = getCategoryById(categoryId);
  return category?.subcategories.find((sub) => sub.id === subcategoryId);
};

export const getAllCategories = (): string[] => {
  return RESOURCE_CATEGORIES.map((cat) => cat.name);
};

export const getSubcategoriesForCategory = (categoryId: string): string[] => {
  const category = getCategoryById(categoryId);
  return category?.subcategories.map((sub) => sub.name) || [];
};

export const getItemsForSubcategory = (categoryId: string, subcategoryId: string): string[] => {
  const subcategory = getSubcategoryById(categoryId, subcategoryId);
  return subcategory?.items || [];
};

// Units of measurement
export const COMMON_UNITS = [
  'kg',
  'g',
  'lbs',
  'oz',
  'liters',
  'ml',
  'gallons',
  'cups',
  'items',
  'pieces',
  'bunches',
  'bags',
  'boxes',
  'hours',
  'days',
  'weeks',
  'months',
];

// Locations (example - would be customized per deployment)
export const COMMON_LOCATIONS = [
  'North Garden',
  'South Garden',
  'Community Center',
  'Tool Shed',
  'Workshop',
  'Greenhouse',
  'Storage Building',
  'Main House',
  'East Field',
  'West Field',
];
