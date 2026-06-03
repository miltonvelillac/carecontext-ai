import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QuestionSection } from "./QuestionSection";

const defaultProps = {
  answer: null,
  isSubmittingAudio: false,
  isSubmittingText: false,
  onSubmitAudio: vi.fn(),
  onSubmitText: vi.fn(),
};

describe("#QuestionSection", () => {
  it("calls onSubmitText with chat query filters", async () => {
    // Arrange
    const user = userEvent.setup();
    const onSubmitText = vi.fn().mockResolvedValue(undefined);
    render(<QuestionSection {...defaultProps} onSubmitText={onSubmitText} />);
    const chatForm = screen.getByLabelText(/written question/i).closest("form")!;

    // Act
    await user.type(
      within(chatForm).getByLabelText(/written question/i),
      "How does sleep affect stress?",
    );
    await user.selectOptions(within(chatForm).getByLabelText(/^language$/i), "en");
    await user.selectOptions(within(chatForm).getByLabelText(/^source$/i), "uploaded");
    await user.clear(within(chatForm).getByLabelText(/^top k$/i));
    await user.type(within(chatForm).getByLabelText(/^top k$/i), "3");
    await user.type(within(chatForm).getByLabelText(/filter tags/i), "sleep, stress");
    await user.click(within(chatForm).getByLabelText(/include tts metadata/i));
    await user.click(within(chatForm).getByRole("button", { name: /ask in chat/i }));

    // Assert
    expect(onSubmitText).toHaveBeenCalledTimes(1);
    expect(onSubmitText).toHaveBeenCalledWith({
      query: "How does sleep affect stress?",
      language: "en",
      top_k: 3,
      filters: {
        source_types: ["uploaded"],
        topic_tags: ["sleep", "stress"],
        language: "en",
      },
      include_tts: true,
    });
  });

  it("calls onSubmitAudio with selected audio file and shared controls", async () => {
    // Arrange
    const user = userEvent.setup();
    const onSubmitAudio = vi.fn().mockResolvedValue(undefined);
    const file = new File(["audio"], "question.mp3", { type: "audio/mpeg" });
    render(<QuestionSection {...defaultProps} onSubmitAudio={onSubmitAudio} />);
    const chatForm = screen.getByLabelText(/written question/i).closest("form")!;
    const audioForm = screen.getByLabelText(/audio file/i).closest("form")!;

    // Act
    await user.selectOptions(within(chatForm).getByLabelText(/^language$/i), "es");
    await user.upload(within(audioForm).getByLabelText(/audio file/i), file);
    await user.click(within(audioForm).getByRole("button", { name: /ask with audio/i }));

    // Assert
    expect(onSubmitAudio).toHaveBeenCalledTimes(1);
    const formData = onSubmitAudio.mock.calls[0][0] as FormData;
    expect(formData.get("file")).toBe(file);
    expect(formData.get("language")).toBe("es");
    expect(formData.get("top_k")).toBe("5");
    expect(formData.get("include_tts")).toBe("false");
  });
});
