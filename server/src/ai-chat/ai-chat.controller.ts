
import { BadRequestException, Body, Controller, Get, Post } from '@nestjs/common';
import { AiChatService } from './ai-chat.service';
import { AiChatRequestDto } from './dto/ai-chat.dto';

@Controller('api/v1/ai')
export class AiChatController {
  constructor(private readonly aiChatService: AiChatService) {}

  @Post('chat')
  async chat(@Body() body: AiChatRequestDto) {
    if (!body?.message || !body.message.trim()) {
      throw new BadRequestException({
        message: 'message is required',
      });
    }

    return this.aiChatService.chat({
      ...body,
      message: body.message.trim(),
    });
  }

  @Get('health')
  async health() {
    return this.aiChatService.health();
  }
}