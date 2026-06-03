import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ContentIngestionSection } from "./ContentIngestionSection";

const defaultProps = {
  documents: [],
  isRefreshing: false,
  isSubmitting: false,
  onRefreshDocuments: vi.fn(),
  onSubmitDocument: vi.fn(),
  onSubmitText: vi.fn(),
};

describe("#ContentIngestionSection", () => {
  it("calls onSubmitDocument with multipart form data when indexing a PDF", async () => {
    // Arrange
    const user = userEvent.setup();
    const onSubmitDocument = vi.fn().mockResolvedValue(undefined);
    const file = new File(["%PDF"], "sleep.pdf", { type: "application/pdf" });
    render(<ContentIngestionSection {...defaultProps} onSubmitDocument={onSubmitDocument} />);
    const pdfPanel = screen.getByText("PDF document").closest("form")!;

    // Act
    await user.upload(within(pdfPanel).getByLabelText(/file/i), file);
    await user.type(within(pdfPanel).getByLabelText(/^title$/i), "Sleep Guide");
    await user.type(within(pdfPanel).getByLabelText(/^tags$/i), "sleep, stress");
    await user.click(within(pdfPanel).getByRole("button", { name: /index pdf/i }));

    // Assert
    expect(onSubmitDocument).toHaveBeenCalledTimes(1);
    const formData = onSubmitDocument.mock.calls[0][0] as FormData;
    expect(formData.get("file")).toBe(file);
    expect(formData.get("title")).toBe("Sleep Guide");
    expect(formData.get("topic_tags")).toBe("sleep, stress");
    expect(formData.get("language")).toBe("auto");
  });

  it("calls onSubmitText with normalized pasted text payload", async () => {
    // Arrange
    const user = userEvent.setup();
    const onSubmitText = vi.fn().mockResolvedValue(undefined);
    render(<ContentIngestionSection {...defaultProps} onSubmitText={onSubmitText} />);
    const textPanel = screen.getByText("Pasted text").closest("form")!;

    // Act
    await user.type(within(textPanel).getByLabelText(/^title$/i), "Session Notes");
    await user.type(within(textPanel).getByLabelText(/^text$/i), "  breathing and sleep notes  ");
    await user.type(within(textPanel).getByLabelText(/^tags$/i), "breathing, sleep");
    await user.selectOptions(within(textPanel).getByLabelText(/^language$/i), "en");
    await user.click(within(textPanel).getByRole("button", { name: /index text/i }));

    // Assert
    expect(onSubmitText).toHaveBeenCalledTimes(1);
    expect(onSubmitText).toHaveBeenCalledWith({
      text: "breathing and sleep notes",
      title: "Session Notes",
      topic_tags: ["breathing", "sleep"],
      language: "en",
    });
  });

  it("calls onRefreshDocuments from the source list action", async () => {
    // Arrange
    const user = userEvent.setup();
    const onRefreshDocuments = vi.fn();
    render(
      <ContentIngestionSection
        {...defaultProps}
        onRefreshDocuments={onRefreshDocuments}
      />,
    );

    // Act
    await user.click(screen.getByRole("button", { name: /refresh sources/i }));

    // Assert
    expect(onRefreshDocuments).toHaveBeenCalledTimes(1);
  });
});
