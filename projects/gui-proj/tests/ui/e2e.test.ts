import { render, screen, fireEvent } from '@testing-library/react';
import App from '../../src/App';

describe('End-to-End UI Tests', () => {
  test('Full UI lifecycle works as expected', () => {
    render(<App />);
    expect(screen.getByText('Initial State')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByText('Next State')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByText('Initial State')).toBeInTheDocument();
  });

  // ...add more end-to-end tests...
});
