/**
 * src/services/forum.ts
 * =====================
 * Service cho module Diễn đàn (Forum).
 * Base URL trỏ đến Forum backend (port 8002).
 */

import apiClient from '@/lib/axios';

const FORUM_BASE = '/api/forum/v1';

class ForumService {
  private baseUrl = FORUM_BASE;

  // TODO: Implement khi Forum backend sẵn sàng
}

export const forumService = new ForumService();
export default forumService;
