export class AiChatRequestDto {
  message!: string;

  /**
   * Optional: nối chat
   */
  conversationId?: string;

  /**
   * Optional: FE có thể gửi context hiện tại, ví dụ:
   * - countryCode đang xem
   * - selected indicator
   * - selected year range
   */
  context?: Record<string, unknown>;
}