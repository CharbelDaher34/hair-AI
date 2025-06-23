# Extension Blocking System

This system prevents browser extensions from interfering with your React application. It includes multiple layers of protection:

## Features

### 1. CSS-based Blocking (`index.css`)
- Hides common extension elements using CSS selectors
- Lightweight and fast
- Always active

### 2. JavaScript-based Blocking (`extension-blocker.ts`)
- Dynamically detects and removes extension elements
- Uses MutationObserver to catch new elements
- Blocks extension scripts
- Configurable and intelligent

### 3. Content Security Policy (`index.html`)
- HTTP headers that restrict what can be loaded
- Prevents extension script injection
- Browser-level protection

### 4. Shadow DOM Isolation (`ShadowDOMWrapper.tsx`)
- Maximum isolation using Shadow DOM
- Completely separates your app from the main DOM
- Most aggressive protection (disabled by default)

## Configuration

Edit `frontend/src/config/extension-config.ts` to customize protection levels:

```typescript
export const DEFAULT_EXTENSION_CONFIG: ExtensionBlockingConfig = {
  enable_css_blocking: true,      // Basic CSS hiding
  enable_js_blocking: true,       // JavaScript detection
  enable_csp_headers: true,       // Content Security Policy
  enable_shadow_dom: false,       // Shadow DOM isolation
  debug_mode: false,              // Console logging
  custom_selectors: [             // Custom extension selectors
    '[data-grammarly]',
    '[data-lastpass]',
    // Add more as needed
  ],
  extension_whitelist: []         // Allow specific extensions
};
```

## Usage

### Basic Usage (Automatic)
The extension blocker is automatically initialized in `main.tsx`. No additional setup required.

### Advanced Usage with Shadow DOM
If you need maximum isolation, you can wrap your app with Shadow DOM:

```tsx
import ShadowDOMWrapper from './components/ShadowDOMWrapper';

// In your component
<ShadowDOMWrapper isolate={true}>
  <YourApp />
</ShadowDOMWrapper>
```

## Debugging

Enable debug mode to see what extensions are being blocked:

```typescript
// In extension-config.ts
debug_mode: true
```

This will log blocked elements to the browser console.

## Common Extension Types Blocked

- **Password Managers**: LastPass, 1Password, Bitwarden
- **Grammar Checkers**: Grammarly, LanguageTool
- **Ad Blockers**: uBlock Origin, AdBlock Plus
- **Shopping**: Honey, Capital One Shopping
- **Developer Tools**: React DevTools, Redux DevTools (can be whitelisted)
- **Accessibility**: Screen readers, color adjusters
- **Custom Extensions**: Any extension with identifiable selectors

## Customization

### Adding Custom Selectors
Add extension-specific selectors to block:

```typescript
custom_selectors: [
  '[data-your-extension]',
  '.your-extension-class',
  '#your-extension-id'
]
```

### Whitelisting Extensions
Allow specific extensions during development:

```typescript
extension_whitelist: [
  'react-developer-tools',
  'redux-devtools'
]
```

## Performance Impact

- **CSS Blocking**: Minimal impact
- **JS Blocking**: Low impact (runs once + on DOM changes)
- **CSP Headers**: No runtime impact
- **Shadow DOM**: Moderate impact (not recommended for all apps)

## Browser Compatibility

- **CSS Blocking**: All modern browsers
- **JS Blocking**: All modern browsers
- **CSP Headers**: All modern browsers
- **Shadow DOM**: Chrome 53+, Firefox 63+, Safari 10+

## Troubleshooting

### Extensions Still Appearing
1. Check browser developer tools for CSP errors
2. Enable debug mode to see what's being blocked
3. Add custom selectors for specific extensions
4. Consider enabling Shadow DOM isolation

### App Features Breaking
1. Disable Shadow DOM isolation
2. Check if legitimate app elements are being blocked
3. Add selectors to extension whitelist
4. Reduce protection level in configuration

### Performance Issues
1. Disable Shadow DOM isolation
2. Reduce custom selectors
3. Disable JS blocking in development

## Best Practices

1. **Start with default configuration** - it covers most cases
2. **Use debug mode during development** - to identify problematic extensions
3. **Test with common extensions** - install popular extensions and test your app
4. **Whitelist development tools** - React DevTools, etc.
5. **Monitor performance** - especially with Shadow DOM enabled
6. **Keep selectors specific** - avoid overly broad selectors that might block legitimate content

## Security Note

This system is designed to improve user experience by preventing extension interference, not to provide security against malicious extensions. Malicious extensions with sufficient privileges can still potentially interfere with your application. 