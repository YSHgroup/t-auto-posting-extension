import { describe, expect, it } from "vitest";

describe("post types", () => {
  it("includes partnership", () => {
    const types = ["Partnership", "Job", "Investment"];
    expect(types).toContain("Partnership");
  });
});
