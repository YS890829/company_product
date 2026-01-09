/**
 * /api/meetings - ミーティングデータ取得
 *
 * Supabase meetingsテーブルからミーティングデータを取得
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
      .from('meetings')
      .select('*')
      .order('date', { ascending: false });

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

    return NextResponse.json({ meetings: data });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
