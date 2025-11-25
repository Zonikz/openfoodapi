# GAINS Mobile App Integration Guide

This document provides code examples and patterns for integrating the GAINS Food Vision API into the GAINS mobile app (Expo React Native).

## Quick Start

### 1. Configure API Endpoint

```typescript
// config/api.ts
export const API_CONFIG = {
  // Development (local)
  baseURL: __DEV__ 
    ? 'http://10.0.2.2:8000'  // Android emulator
    : 'http://localhost:8000', // iOS simulator
  
  // Production (self-hosted)
  // baseURL: 'https://your-api-domain.com',
  
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  }
};
```

---

## API Integration Patterns

### 1. Image Classification Flow

```typescript
// services/foodVision.ts
import axios from 'axios';
import { API_CONFIG } from '../config/api';

export interface ClassificationResult {
  label: string;
  score: number;
}

export interface ClassifyResponse {
  model: string;
  top_k: ClassificationResult[];
  inference_ms: number;
}

export async function classifyFoodImage(
  imageUri: string,
  topK: number = 5
): Promise<ClassifyResponse> {
  try {
    // Create form data
    const formData = new FormData();
    formData.append('file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'food.jpg',
    } as any);

    // Call API
    const response = await axios.post<ClassifyResponse>(
      `${API_CONFIG.baseURL}/api/classify?top_k=${topK}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: API_CONFIG.timeout,
      }
    );

    return response.data;
  } catch (error) {
    console.error('Classification failed:', error);
    throw new Error('Failed to classify food image');
  }
}
```

**Usage in Component**:
```typescript
// screens/CameraScreen.tsx
import { Camera } from 'expo-camera';
import { classifyFoodImage } from '../services/foodVision';

const CameraScreen = () => {
  const [predictions, setPredictions] = useState<ClassificationResult[]>([]);
  const [loading, setLoading] = useState(false);

  const takePicture = async () => {
    if (!camera) return;
    
    try {
      setLoading(true);
      
      // Capture image
      const photo = await camera.takePictureAsync({
        quality: 0.8,
        base64: false,
      });
      
      // Classify
      const result = await classifyFoodImage(photo.uri, 5);
      
      setPredictions(result.top_k);
      console.log(`Inference time: ${result.inference_ms}ms`);
      
      // Navigate to selection screen
      navigation.navigate('FoodSelection', { predictions });
      
    } catch (error) {
      Alert.alert('Error', 'Failed to classify food');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Camera ref={ref => camera = ref} style={styles.camera} />
      <Button onPress={takePicture} disabled={loading}>
        {loading ? 'Processing...' : 'Capture'}
      </Button>
    </View>
  );
};
```

---

### 2. Map to Canonical Food

```typescript
// services/foodVision.ts
export interface CanonicalFood {
  canonical_name: string;
  source: string;
  source_id: string;
  per_100g: {
    energy_kcal?: number;
    protein_g?: number;
    carb_g?: number;
    fat_g?: number;
    fiber_g?: number;
    sugar_g?: number;
    saturated_fat_g?: number;
    sodium_mg?: number;
  };
  servings?: Array<{ name: string; grams: number }>;
  enrichment?: {
    nova?: number;
    nutriscore?: string;
    additives?: string[];
  };
}

export async function mapToCanonicalFood(
  food101Label: string,
  country: string = 'UK'
): Promise<CanonicalFood> {
  try {
    const response = await axios.post<CanonicalFood>(
      `${API_CONFIG.baseURL}/api/map-to-food`,
      {
        query: food101Label,
        country: country,
      }
    );

    return response.data;
  } catch (error) {
    console.error('Mapping failed:', error);
    throw new Error('Failed to map to canonical food');
  }
}
```

**Usage**:
```typescript
// screens/FoodSelectionScreen.tsx
const FoodSelectionScreen = ({ route, navigation }) => {
  const { predictions } = route.params;
  
  const handleSelect = async (prediction: ClassificationResult) => {
    try {
      // Map to canonical food
      const canonicalFood = await mapToCanonicalFood(prediction.label);
      
      // Navigate to portion estimation
      navigation.navigate('PortionEstimation', { 
        food: canonicalFood,
        confidence: prediction.score 
      });
      
    } catch (error) {
      Alert.alert('Error', 'Failed to get food details');
    }
  };

  return (
    <FlatList
      data={predictions}
      renderItem={({ item }) => (
        <TouchableOpacity onPress={() => handleSelect(item)}>
          <View style={styles.predictionCard}>
            <Text>{item.label.replace(/_/g, ' ')}</Text>
            <Text>{(item.score * 100).toFixed(1)}% confidence</Text>
          </View>
        </TouchableOpacity>
      )}
    />
  );
};
```

---

### 3. GAINS Scoring

```typescript
// services/foodVision.ts
export interface GAINSScore {
  macros: {
    energy_kcal: number;
    protein_g: number;
    carb_g: number;
    fat_g: number;
  };
  score: {
    protein_density: number;
    carb_quality: number;
    fat_quality: number;
    processing: number;
    transparency: number;
    overall: number;
  };
  grade: string;
  explanation: string;
}

export async function calculateGAINSScore(
  canonicalId: string,
  grams: number
): Promise<GAINSScore> {
  try {
    const response = await axios.post<GAINSScore>(
      `${API_CONFIG.baseURL}/api/score/gains`,
      {
        canonical_id: canonicalId,
        grams: grams,
      }
    );

    return response.data;
  } catch (error) {
    console.error('Scoring failed:', error);
    throw new Error('Failed to calculate GAINS score');
  }
}
```

**Usage**:
```typescript
// screens/PortionEstimationScreen.tsx
const PortionEstimationScreen = ({ route }) => {
  const { food } = route.params;
  const [grams, setGrams] = useState(100);
  const [score, setScore] = useState<GAINSScore | null>(null);

  const estimatePortion = async (estimatedGrams: number) => {
    try {
      setGrams(estimatedGrams);
      
      // Calculate GAINS score
      const gainsScore = await calculateGAINSScore(
        food.source_id,
        estimatedGrams
      );
      
      setScore(gainsScore);
      
    } catch (error) {
      Alert.alert('Error', 'Failed to calculate score');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.foodName}>{food.canonical_name}</Text>
      
      {/* Portion slider */}
      <Slider
        value={grams}
        onValueChange={estimatePortion}
        minimumValue={50}
        maximumValue={500}
        step={10}
      />
      
      {/* GAINS Score Display */}
      {score && (
        <View style={styles.scoreCard}>
          <Text style={styles.grade}>{score.grade}</Text>
          <Text style={styles.overall}>
            Overall: {(score.score.overall * 100).toFixed(0)}
          </Text>
          
          <View style={styles.breakdown}>
            <ScoreBar label="Protein" value={score.score.protein_density} />
            <ScoreBar label="Carbs" value={score.score.carb_quality} />
            <ScoreBar label="Fats" value={score.score.fat_quality} />
            <ScoreBar label="Processing" value={score.score.processing} />
          </View>
          
          <Text style={styles.macros}>
            {score.macros.energy_kcal} kcal | 
            P: {score.macros.protein_g}g | 
            C: {score.macros.carb_g}g | 
            F: {score.macros.fat_g}g
          </Text>
        </View>
      )}
    </View>
  );
};
```

---

### 4. Barcode Scanning

```typescript
// services/foodVision.ts
export async function lookupBarcode(barcode: string): Promise<CanonicalFood> {
  try {
    const response = await axios.get<CanonicalFood>(
      `${API_CONFIG.baseURL}/api/barcode/${barcode}`
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      throw new Error('Product not found');
    }
    throw new Error('Barcode lookup failed');
  }
}
```

**Usage**:
```typescript
// screens/BarcodeScanScreen.tsx
import { BarCodeScanner } from 'expo-barcode-scanner';

const BarcodeScanScreen = ({ navigation }) => {
  const handleBarCodeScanned = async ({ data }: { data: string }) => {
    try {
      // Look up product
      const product = await lookupBarcode(data);
      
      // Navigate to portion estimation
      navigation.navigate('PortionEstimation', { 
        food: product,
        fromBarcode: true 
      });
      
    } catch (error) {
      if (error.message === 'Product not found') {
        Alert.alert(
          'Not Found',
          'This product is not in our database. Try manual entry.',
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert('Error', 'Failed to look up barcode');
      }
    }
  };

  return (
    <BarCodeScanner
      onBarCodeScanned={handleBarCodeScanned}
      style={StyleSheet.absoluteFillObject}
    />
  );
};
```

---

### 5. Fuzzy Search

```typescript
// services/foodVision.ts
export async function searchFoods(
  query: string,
  limit: number = 10
): Promise<CanonicalFood[]> {
  try {
    const response = await axios.get(
      `${API_CONFIG.baseURL}/api/foods/search`,
      {
        params: { q: query, limit },
      }
    );

    return response.data.results;
  } catch (error) {
    console.error('Search failed:', error);
    return [];
  }
}
```

**Usage**:
```typescript
// components/FoodSearchBar.tsx
const FoodSearchBar = ({ onSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CanonicalFood[]>([]);
  const [loading, setLoading] = useState(false);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length > 2) {
        setLoading(true);
        const foods = await searchFoods(query, 10);
        setResults(foods);
        setLoading(false);
      } else {
        setResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <View>
      <TextInput
        placeholder="Search foods (e.g., chiken currie)"
        value={query}
        onChangeText={setQuery}
      />
      
      {loading && <ActivityIndicator />}
      
      <FlatList
        data={results}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => onSelect(item)}>
            <Text>{item.canonical_name}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
};
```

---

## Error Handling

### Recommended Error Patterns

```typescript
// utils/errorHandler.ts
export function handleAPIError(error: any): string {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again.';
    }
    
    if (error.response) {
      // Server responded with error
      switch (error.response.status) {
        case 422:
          return error.response.data.detail || 'Invalid input';
        case 503:
          return 'Service temporarily unavailable';
        case 500:
          return 'Server error. Please try again.';
        default:
          return 'An error occurred';
      }
    } else if (error.request) {
      // No response from server
      return 'Cannot reach server. Check your connection.';
    }
  }
  
  return 'An unexpected error occurred';
}
```

---

## Performance Tips

### 1. Image Optimization
```typescript
// Before sending to API
const optimizeImage = async (uri: string) => {
  const manipResult = await ImageManipulator.manipulateAsync(
    uri,
    [{ resize: { width: 1024 } }], // Resize to max 1024px width
    { compress: 0.8, format: SaveFormat.JPEG }
  );
  return manipResult.uri;
};
```

### 2. Timeout Configuration
```typescript
// Adjust timeouts for different operations
const TIMEOUTS = {
  classify: 10000,    // 10 seconds (image processing)
  mapping: 5000,      // 5 seconds (database lookup)
  search: 3000,       // 3 seconds (search)
  barcode: 5000,      // 5 seconds (barcode lookup)
};
```

### 3. Retry Logic
```typescript
const retryRequest = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  throw new Error('Max retries exceeded');
};
```

---

## Testing

### Mock API for Development

```typescript
// services/__mocks__/foodVision.ts
export const classifyFoodImage = jest.fn().mockResolvedValue({
  model: 'food101-resnet50',
  top_k: [
    { label: 'chicken_curry', score: 0.78 },
    { label: 'butter_chicken', score: 0.14 },
  ],
  inference_ms: 42,
});

export const mapToCanonicalFood = jest.fn().mockResolvedValue({
  canonical_name: 'Chicken curry',
  source: 'cofid',
  source_id: 'COFID:1001',
  per_100g: {
    energy_kcal: 148,
    protein_g: 16.5,
    carb_g: 5.8,
    fat_g: 6.1,
  },
});
```

---

## Health Check

```typescript
// services/foodVision.ts
export async function checkAPIHealth(): Promise<boolean> {
  try {
    const response = await axios.get(
      `${API_CONFIG.baseURL}/health`,
      { timeout: 3000 }
    );
    
    return response.data.status === 'healthy';
  } catch {
    return false;
  }
}

// Usage: Check on app start
useEffect(() => {
  checkAPIHealth().then(healthy => {
    if (!healthy) {
      Alert.alert(
        'API Unavailable',
        'Food recognition service is not available. Some features may not work.'
      );
    }
  });
}, []);
```

---

## Complete Flow Example

```typescript
// The complete GAINS food logging flow
const logFood = async (imageUri: string) => {
  try {
    // Step 1: Classify image
    const classification = await classifyFoodImage(imageUri, 5);
    
    // Step 2: User selects from predictions
    const selectedLabel = await showPredictionPicker(classification.top_k);
    
    // Step 3: Map to canonical food
    const canonicalFood = await mapToCanonicalFood(selectedLabel);
    
    // Step 4: Estimate portion (user input)
    const portionGrams = await showPortionEstimator();
    
    // Step 5: Calculate GAINS score
    const score = await calculateGAINSScore(
      canonicalFood.source_id,
      portionGrams
    );
    
    // Step 6: Save to diary
    await saveFoodDiary({
      food: canonicalFood,
      grams: portionGrams,
      score: score,
      timestamp: new Date(),
    });
    
    // Step 7: Show success
    showSuccessMessage(`Logged ${canonicalFood.canonical_name}`);
    
  } catch (error) {
    Alert.alert('Error', handleAPIError(error));
  }
};
```

---

## Support

For issues or questions:
- GitHub: [Your repo URL]
- Documentation: See README.md
- API Docs: http://localhost:8000/docs
