import { render, unmountComponentAtNode } from 'react-dom';
import ComponentA from '../../src/components/ComponentA';

let container: HTMLElement | null = null;

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

afterEach(() => {
  if (container) {
    unmountComponentAtNode(container);
    container.remove();
    container = null;
  }
});

describe('Component Lifecycle Tests', () => {
  test('ComponentA mounts and unmounts without errors', () => {
    render(<ComponentA />, container);
    expect(container?.textContent).toContain('Expected Text');
    unmountComponentAtNode(container!);
    expect(container?.textContent).toBe('');
  });

  // ...add lifecycle tests for other components...
});
