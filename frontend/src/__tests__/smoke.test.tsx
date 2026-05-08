import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Vitest smoke test', () => {
  it('renders simple component', () => {
    render(<div>hello vitest</div>);
    expect(screen.getByText('hello vitest')).toBeInTheDocument();
  });
});
