/**
 * /api/deals - 商談データ取得
 *
 * Supabase dealsテーブルから商談データを取得
 * クエリパラメータ: company_id（オプション）
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
    const companyId = searchParams.get('company_id');

    let query = supabase
      .from('deals')
      .select(`
        *,
        company_name:companies(name)
      `)
      .order('created_at', { ascending: false });

    if (companyId) {
      query = query.eq('company_id', companyId);
    }

    const { data, error } = await query;

    if (error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }

    // Flatten company_name from join
    const deals = data?.map((deal: any) => ({
      ...deal,
      company_name: deal.company_name?.[0]?.name || deal.company_name?.name || 'Unknown'
    }));

    return NextResponse.json({ deals });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
