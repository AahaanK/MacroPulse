import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useTheme } from "../hooks/useTheme";

describe("useTheme Hook", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("defaults to light theme when matchMedia is false and toggles correctly", () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("macropulse-theme")).toBe("dark");

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.isDark).toBe(false);
    expect(localStorage.getItem("macropulse-theme")).toBe("light");
  });
});
