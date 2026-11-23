import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Banner } from "../components/Banner";

describe("Banner Component", () => {
  it("renders when message is present", () => {
    render(<Banner message="Demonstration data — not for research conclusions" />);
    expect(
      screen.getByText("Demonstration data — not for research conclusions")
    ).toBeInTheDocument();
  });

  it("does not render when message is null or empty", () => {
    const { container } = render(<Banner message={null} />);
    expect(container.firstChild).toBeNull();
  });
});
