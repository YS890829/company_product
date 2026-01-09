/**
 * /api/emails - メールデータ取得
 *
 * Supabase emailsテーブルからメールデータを取得
 * クエリパラメータ: deal_id（オプション）
 */

import { createClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    const { searchParams } = new URL(request.url);
    const dealId = searchParams.get('deal_id');

    let query = supabase
      .from('emails')
      .select('*')
      .order('sent_at', { ascending: false });

    if (dealId) {
      query = query.eq('deal_id', dealId);
    }

    const { data, error } = await query;

    if (error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({ emails: data });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
